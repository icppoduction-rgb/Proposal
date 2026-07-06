"""Shared helpers for Stage Three normalized-event feature extractors."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.compute as pc


LABEL_COLUMNS: tuple[str, ...] = (
    "label_binary",
    "label_family",
    "label_subtype",
    "label_source",
    "label_status",
    "label_confidence",
    "label_mapping_rule_id",
)
TRACEABILITY_COLUMNS: tuple[str, ...] = (
    "sample_uid",
    "normalized_artifact_id",
    "source_event_uid_refs",
    "source_normalized_path",
    "dataset_id",
    "role",
    "branch",
    "feature_group",
    "feature_schema_name",
    "feature_schema_version",
    "created_at",
)
BASE_NORMALIZED_COLUMNS: tuple[str, ...] = (
    "event_uid",
    "event_timestamp",
    "timestamp",
    "event_order",
    "event_index",
    "timestamp_type",
    "event_type",
    "raw_event_name",
    "modality",
    "source_format",
    "features_json",
    "raw_fields_json",
    "metadata_json",
    *LABEL_COLUMNS,
)
DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"


def select_existing_columns(schema: pa.Schema, requested_columns: Iterable[str]) -> list[str]:
    """Return a stable projection that keeps only columns present in an artifact."""
    available = set(schema.names)
    return [column for column in dict.fromkeys(requested_columns) if column in available]


def traceability_payload(
    *,
    table: pa.Table,
    normalized_artifact_id: int,
    dataset_id: int,
    role: str,
    branch: str,
    feature_group: str,
    source_normalized_path: str | Path,
) -> dict[str, Any]:
    """Build deterministic traceability columns for one extracted feature batch."""
    event_uids = string_values(table, "event_uid")
    sample_uids = [
        f"na:{normalized_artifact_id}:event:{event_uid}" if event_uid else f"na:{normalized_artifact_id}:row:{index}"
        for index, event_uid in enumerate(event_uids)
    ]
    return {
        "sample_uid": sample_uids,
        "normalized_artifact_id": [normalized_artifact_id] * table.num_rows,
        "source_event_uid_refs": [[event_uid] if event_uid else [] for event_uid in event_uids],
        "source_normalized_path": [str(source_normalized_path)] * table.num_rows,
        "dataset_id": [dataset_id] * table.num_rows,
        "role": [role] * table.num_rows,
        "branch": [branch] * table.num_rows,
        "feature_group": [feature_group] * table.num_rows,
        "feature_schema_name": ["feature_artifact"] * table.num_rows,
        "feature_schema_version": ["v1"] * table.num_rows,
        "created_at": [DETERMINISTIC_CREATED_AT] * table.num_rows,
    }


def labels_payload(table: pa.Table) -> dict[str, list[Any]]:
    """Return nullable label columns without treating missing labels as benign."""
    return {column: nullable_values(table, column) for column in LABEL_COLUMNS}


def nullable_values(table: pa.Table, column: str) -> list[Any]:
    """Return a pylist for a nullable column, or all nulls when absent."""
    if column not in table.column_names:
        return [None] * table.num_rows
    return table.column(column).to_pylist()


def string_values(table: pa.Table, column: str) -> list[str | None]:
    """Return stripped string values for a nullable column."""
    values = nullable_values(table, column)
    return [None if value is None else str(value).strip() for value in values]


def numeric_values(table: pa.Table, column: str) -> list[float | None]:
    """Return numeric values with invalid inputs preserved as nulls."""
    values = nullable_values(table, column)
    return [coerce_float(value) for value in values]


def timestamp_values(table: pa.Table) -> list[datetime | None]:
    """Read event timestamps from either Stage Two naming convention."""
    for column in ("event_timestamp", "timestamp"):
        if column in table.column_names:
            return [coerce_datetime(value) for value in table.column(column).to_pylist()]
    return [None] * table.num_rows


def order_values(table: pa.Table) -> list[int | None]:
    """Read event order from either Stage Two naming convention."""
    for column in ("event_order", "event_index"):
        if column in table.column_names:
            return [coerce_int(value) for value in table.column(column).to_pylist()]
    return [None] * table.num_rows


def json_rows(table: pa.Table, column: str) -> list[dict[str, Any]]:
    """Return JSON object rows from a normalized JSON/string/struct column."""
    rows: list[dict[str, Any]] = []
    for value in nullable_values(table, column):
        if isinstance(value, dict):
            rows.append(value)
        elif isinstance(value, str):
            try:
                loaded = json.loads(value)
            except json.JSONDecodeError:
                rows.append({})
            else:
                rows.append(loaded if isinstance(loaded, dict) else {})
        else:
            rows.append({})
    return rows


def first_value(row: dict[str, Any], keys: Iterable[str]) -> Any:
    """Pick the first non-empty value from a nested JSON-like row."""
    for key in keys:
        value = nested_value(row, key)
        if value not in (None, ""):
            return value
    return None


def nested_value(row: dict[str, Any], dotted_key: str) -> Any:
    """Read dotted keys from nested dicts and literal dotted-key payloads."""
    if dotted_key in row:
        return row[dotted_key]
    current: Any = row
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def stable_hash_int(value: Any, *, modulo: int = 2**31 - 1) -> int | None:
    """Return a deterministic non-cryptographic feature hash bucket."""
    if value in (None, ""):
        return None
    digest = hashlib.sha256(str(value).strip().lower().encode("utf-8", errors="replace")).hexdigest()
    return int(digest[:16], 16) % modulo


def coerce_float(value: Any) -> float | None:
    """Convert numeric-looking values to float."""
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return float(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def coerce_int(value: Any) -> int | None:
    """Convert integer-looking values to int."""
    number = coerce_float(value)
    if number is None:
        return None
    return int(number)


def coerce_datetime(value: Any) -> datetime | None:
    """Convert supported timestamp representations to timezone-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    return None


def datetime_to_epoch_seconds(value: datetime | None) -> float | None:
    """Return UTC epoch seconds for a datetime value."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def missing_ratios(table: pa.Table, columns: tuple[str, ...]) -> dict[str, float]:
    """Calculate missing ratios for selected feature columns."""
    ratios: dict[str, float] = {}
    if table.num_rows == 0:
        return {column: 0.0 for column in columns}
    for column in columns:
        if column not in table.column_names:
            ratios[column] = 1.0
            continue
        null_markers = pc.cast(pc.is_null(table.column(column)), pa.int64())
        null_count = pc.sum(null_markers).as_py()
        ratios[column] = float(null_count or 0) / table.num_rows
    return ratios


def unsupported_field_warnings(
    *,
    table: pa.Table,
    supported_columns: Iterable[str],
    feature_group: str,
) -> list[str]:
    """Summarize unsupported source columns without turning them into X features."""
    supported = set(supported_columns)
    ignored = sorted(column for column in table.column_names if column not in supported)
    if not ignored:
        return []
    return [
        f"{feature_group}: ignored unsupported normalized source fields: {', '.join(ignored[:20])}"
        + (" ..." if len(ignored) > 20 else "")
    ]
