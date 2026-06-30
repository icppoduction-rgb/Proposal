"""Shared normalized event helpers for Stage Two parsers."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LABEL_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "label_binary",
        "label_family",
        "label_subtype",
        "label_source",
        "label_status",
        "label_confidence",
        "label_mapping_rule_id",
    }
)
CSV_HELPER_FILE_NAMES: frozenset[str] = frozenset({"feature_descr.csv", "ground_truth.csv"})
README_LIKE_FILE_NAMES: frozenset[str] = frozenset(
    {
        "readme",
        "readme.txt",
        "readme.md",
        "readme.rst",
        "README",
        "README.txt",
        "README.md",
        "README.rst",
    }
)
README_HEADING_TOKENS: tuple[str, ...] = (
    "readme",
    "overview",
    "dataset description",
    "data description",
    "license",
    "citation",
)
SYSCALL_REFERENCE_NAME_TOKENS: tuple[str, ...] = ("syscall", "list")


@dataclass(frozen=True)
class HelperFileDecision:
    """Classification for helper/context files that should not be parsed as telemetry."""

    is_helper: bool
    helper_type: str | None = None
    reason: str | None = None
    emit_metadata_event: bool = False


def generate_event_uid(
    context: Any,
    event_index: int | str | None,
    entity: Any = None,
    *extra_parts: Any,
) -> str:
    """Generate a deterministic event UID from source path, event index, and entity."""
    parts = [
        getattr(context, "source_file_path", ""),
        "" if event_index is None else str(event_index),
        "" if entity is None else str(entity),
        *(str(part) for part in extra_parts if part is not None),
    ]
    raw = ":".join(parts).encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def build_traceability_fields(
    context: Any,
    *,
    parser_name: str,
    parser_version: str,
    schema_name: str,
    schema_version: str,
) -> dict[str, Any]:
    """Build canonical raw-file and parser traceability fields."""
    return {
        "dataset_id": getattr(context, "dataset_id", None),
        "file_id": getattr(context, "file_id", None),
        "dataset_name": getattr(context, "dataset_name"),
        "dataset_role": getattr(context, "dataset_role"),
        "branch": getattr(context, "branch"),
        "source_format": getattr(context, "source_format"),
        "source_file_path": getattr(context, "source_file_path"),
        "source_file_hash": getattr(context, "source_file_hash", None),
        "parser_name": parser_name,
        "parser_version": parser_version,
        "parser_run_id": getattr(context, "parser_run_id", None),
        "schema_name": schema_name,
        "schema_version": schema_version,
    }


def build_timestamp_fields(
    *,
    timestamp: datetime | None = None,
    timestamp_source: str | None = None,
    timestamp_type: str | None = None,
    event_index: int | None = None,
) -> dict[str, Any]:
    """Build canonical timestamp fields with safe defaults."""
    resolved_timestamp_type = timestamp_type
    if resolved_timestamp_type is None:
        if timestamp is not None:
            resolved_timestamp_type = "absolute"
        elif event_index is not None:
            resolved_timestamp_type = "event_order"
        else:
            resolved_timestamp_type = "missing"
    return {
        "timestamp": timestamp,
        "timestamp_source": timestamp_source,
        "timestamp_type": resolved_timestamp_type,
        "event_index": event_index,
    }


def build_default_label_fields(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build default normalized label fields and apply explicit parser overrides."""
    fields: dict[str, Any] = {
        "label_binary": None,
        "label_family": None,
        "label_subtype": None,
        "label_source": "none",
        "label_status": "unlabeled",
        "label_confidence": None,
        "label_mapping_rule_id": None,
    }
    if overrides:
        fields.update({key: overrides[key] for key in LABEL_FIELD_NAMES if key in overrides})
    return fields


def merge_json_objects(
    *payloads: Mapping[str, Any] | None,
    empty_as_none: bool = False,
) -> dict[str, Any] | None:
    """Merge JSON object payloads while dropping empty string and None values."""
    merged: dict[str, Any] = {}
    for payload in payloads:
        if not payload:
            continue
        for key, value in payload.items():
            if value in ("", None):
                continue
            merged[str(key)] = compact_json_value(value)
    if not merged and empty_as_none:
        return None
    return merged


def compact_json_value(value: Any) -> Any:
    """Return a JSON-safe value with empty nested values removed."""
    if isinstance(value, Mapping):
        return {
            str(key): compact_json_value(item)
            for key, item in value.items()
            if item not in ("", None)
        }
    if isinstance(value, list):
        return [compact_json_value(item) for item in value if item not in ("", None)]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def classify_helper_file(
    path: str | Path,
    *,
    source_format: str | None = None,
    sample_text: str | None = None,
) -> HelperFileDecision:
    """Return helper/context-file classification for parser fallback decisions."""
    file_name = Path(path).name
    lower_name = file_name.lower()
    if lower_name in CSV_HELPER_FILE_NAMES:
        return HelperFileDecision(
            is_helper=True,
            helper_type=lower_name,
            reason=f"{file_name} is context metadata, not a telemetry event stream",
            emit_metadata_event=True,
        )
    if _is_syscall_reference_file_name(lower_name, source_format=source_format):
        return HelperFileDecision(
            is_helper=True,
            helper_type="syscall_reference",
            reason=f"{file_name} is a syscall reference list, not a telemetry event stream",
            emit_metadata_event=False,
        )
    if is_readme_like_file(path, source_format=source_format, sample_text=sample_text):
        return HelperFileDecision(
            is_helper=True,
            helper_type="readme_like",
            reason=f"{file_name} is README-like helper text, not a telemetry event stream",
            emit_metadata_event=False,
        )
    return HelperFileDecision(is_helper=False)


def is_readme_like_file(
    path: str | Path,
    *,
    source_format: str | None = None,
    sample_text: str | None = None,
) -> bool:
    """Return True for README-like helper text that lands in a parser bucket."""
    file_name = Path(path).name
    lower_name = file_name.lower()
    if lower_name in {name.lower() for name in README_LIKE_FILE_NAMES}:
        return True
    suffix = Path(path).suffix.lower()
    if source_format not in {None, "txt", "log"} and suffix not in {".txt", ".md", ".rst", ""}:
        return False
    if sample_text is None:
        return False
    first_lines = [line.strip().lower() for line in sample_text.splitlines() if line.strip()][:5]
    if not first_lines:
        return False
    first_text = " ".join(first_lines)
    return any(token in first_text for token in README_HEADING_TOKENS)


def _is_syscall_reference_file_name(lower_name: str, *, source_format: str | None) -> bool:
    if source_format not in {None, "txt"}:
        return False
    return lower_name.endswith(".txt") and all(token in lower_name for token in SYSCALL_REFERENCE_NAME_TOKENS)


def parser_report_warning(
    *,
    status: str,
    reason: str,
    helper_type: str | None = None,
) -> str:
    """Return a compact parser-report warning suitable for ParserResult.warnings."""
    parts = [f"parser_report_status={status}", f"reason={reason}"]
    if helper_type:
        parts.append(f"helper_type={helper_type}")
    return "; ".join(parts)


def helper_file_metadata(
    *,
    decision: HelperFileDecision,
    action: str,
    rows_read: int | None = None,
) -> dict[str, Any] | None:
    """Build compact metadata for helper/context files."""
    if not decision.is_helper:
        return None
    return merge_json_objects(
        {
            "helper_file": True,
            "helper_type": decision.helper_type,
            "helper_action": action,
            "parser_reason": decision.reason,
            "rows_read": rows_read,
        },
        empty_as_none=True,
    )


def build_normalized_event(
    context: Any,
    *,
    parser_name: str,
    parser_version: str,
    schema_name: str,
    schema_version: str,
    **values: Any,
) -> dict[str, Any]:
    """Build a normalized event using the canonical Stage Two event contract."""
    event_values = dict(values)
    event_index = event_values.pop("event_index", None)
    timestamp = event_values.pop("timestamp", None)
    timestamp_source = event_values.pop("timestamp_source", None)
    timestamp_type = event_values.pop("timestamp_type", None)
    created_at = event_values.pop("created_at", None) or datetime.now(timezone.utc)
    event_uid = event_values.pop("event_uid", None)
    raw_fields_json = event_values.pop("raw_fields_json", None)
    metadata_json = event_values.pop("metadata_json", None)
    features_json = event_values.pop("features_json", None)
    label_overrides = {
        key: event_values.pop(key)
        for key in tuple(event_values)
        if key in LABEL_FIELD_NAMES
    }

    if event_uid is None:
        event_uid = generate_event_uid(
            context,
            event_index,
            event_values.get("entity_id") or event_values.get("event_type"),
        )

    event = {
        "event_uid": event_uid,
        **build_traceability_fields(
            context,
            parser_name=parser_name,
            parser_version=parser_version,
            schema_name=schema_name,
            schema_version=schema_version,
        ),
        **build_timestamp_fields(
            timestamp=timestamp,
            timestamp_source=timestamp_source,
            timestamp_type=timestamp_type,
            event_index=event_index,
        ),
        **build_default_label_fields(label_overrides),
        "features_json": features_json,
        "raw_fields_json": raw_fields_json,
        "metadata_json": metadata_json,
        "created_at": created_at,
    }
    event.update(event_values)
    return event
