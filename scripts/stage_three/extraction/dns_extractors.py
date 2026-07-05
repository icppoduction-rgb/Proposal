"""DNS MVP feature extractors for normalized Parquet artifacts."""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timezone
from statistics import pstdev
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc


DNS_MVP_FEATURE_GROUPS: tuple[str, ...] = ("dns_lexical", "dns_entropy", "dns_temporal")
DNS_MVP_FEATURES: dict[str, tuple[str, ...]] = {
    "dns_lexical": (
        "dns_query_length",
        "dns_subdomain_length",
        "dns_label_count",
        "dns_label_avg_len",
        "dns_label_max_len",
        "dns_digit_count",
        "dns_special_char_count",
    ),
    "dns_entropy": ("dns_entropy",),
    "dns_temporal": (
        "dns_queries_per_window",
        "dns_inter_query_interval_mean",
        "dns_inter_query_interval_std",
        "dns_burst_score",
    ),
}
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
LABEL_COLUMNS: tuple[str, ...] = (
    "label_binary",
    "label_family",
    "label_subtype",
    "label_source",
    "label_status",
    "label_confidence",
    "label_mapping_rule_id",
)
DNS_SOURCE_CANDIDATES: tuple[str, ...] = ("domain", "dns_query", "query", "qname")
BASE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "event_uid",
    "event_timestamp",
    "event_order",
    "domain",
    "dns_query",
    "query",
    "qname",
    *LABEL_COLUMNS,
)


def dns_feature_columns(feature_group: str) -> tuple[str, ...]:
    """Return feature columns produced for a DNS MVP feature group."""
    try:
        return DNS_MVP_FEATURES[feature_group]
    except KeyError as exc:
        allowed = ", ".join(DNS_MVP_FEATURE_GROUPS)
        raise ValueError(f"unsupported DNS MVP feature_group={feature_group!r}; allowed: {allowed}") from exc


def required_dns_columns(feature_group: str) -> tuple[str, ...]:
    """Return normalized input columns needed for a DNS MVP extractor."""
    dns_feature_columns(feature_group)
    return BASE_REQUIRED_COLUMNS


def extract_dns_features_from_table(
    table: pa.Table,
    *,
    feature_group: str,
    normalized_artifact_id: int,
    dataset_id: int,
    role: str,
    source_normalized_path: str,
) -> pa.Table:
    """Extract DNS MVP features for one bounded Arrow table."""
    feature_columns = dns_feature_columns(feature_group)
    row_count = table.num_rows
    domains = _domain_values(table)
    event_uids = _string_column(table, "event_uid", row_count)
    event_timestamps = _timestamp_values(table, "event_timestamp", row_count)
    labels = {column: _nullable_column(table, column, row_count) for column in LABEL_COLUMNS}

    payload: dict[str, Any] = _traceability_payload(
        event_uids=event_uids,
        normalized_artifact_id=normalized_artifact_id,
        dataset_id=dataset_id,
        role=role,
        feature_group=feature_group,
        source_normalized_path=source_normalized_path,
    )
    if feature_group == "dns_lexical":
        payload.update(_extract_lexical(domains))
    elif feature_group == "dns_entropy":
        payload.update({"dns_entropy": [_entropy(domain) for domain in domains]})
    elif feature_group == "dns_temporal":
        payload.update(_extract_temporal(event_timestamps))
    for column, values in labels.items():
        payload[column] = values
    # Preserve the catalog feature order after traceability fields.
    ordered = {
        **{column: payload[column] for column in TRACEABILITY_COLUMNS},
        **{column: payload[column] for column in feature_columns},
        **{column: payload[column] for column in LABEL_COLUMNS},
    }
    return pa.table(ordered)


def _traceability_payload(
    *,
    event_uids: list[str | None],
    normalized_artifact_id: int,
    dataset_id: int,
    role: str,
    feature_group: str,
    source_normalized_path: str,
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    sample_uids = [
        f"na:{normalized_artifact_id}:event:{event_uid}" if event_uid else f"na:{normalized_artifact_id}:row:{index}"
        for index, event_uid in enumerate(event_uids)
    ]
    return {
        "sample_uid": sample_uids,
        "normalized_artifact_id": [normalized_artifact_id] * len(event_uids),
        "source_event_uid_refs": [[event_uid] if event_uid else [] for event_uid in event_uids],
        "source_normalized_path": [source_normalized_path] * len(event_uids),
        "dataset_id": [dataset_id] * len(event_uids),
        "role": [role] * len(event_uids),
        "branch": ["dns"] * len(event_uids),
        "feature_group": [feature_group] * len(event_uids),
        "feature_schema_name": ["feature_artifact"] * len(event_uids),
        "feature_schema_version": ["v1"] * len(event_uids),
        "created_at": [created_at] * len(event_uids),
    }


def _extract_lexical(domains: list[str]) -> dict[str, list[int | float]]:
    query_lengths: list[int] = []
    subdomain_lengths: list[int] = []
    label_counts: list[int] = []
    label_avg_lens: list[float] = []
    label_max_lens: list[int] = []
    digit_counts: list[int] = []
    special_counts: list[int] = []
    for domain in domains:
        labels = [label for label in domain.strip(".").split(".") if label]
        label_lengths = [len(label) for label in labels]
        query_lengths.append(len(domain))
        subdomain = ".".join(labels[:-2]) if len(labels) > 2 else ""
        subdomain_lengths.append(len(subdomain))
        label_counts.append(len(labels))
        label_avg_lens.append(sum(label_lengths) / len(label_lengths) if label_lengths else 0.0)
        label_max_lens.append(max(label_lengths) if label_lengths else 0)
        digit_counts.append(sum(1 for char in domain if char.isdigit()))
        special_counts.append(len(re.findall(r"[^A-Za-z0-9.]", domain)))
    return {
        "dns_query_length": query_lengths,
        "dns_subdomain_length": subdomain_lengths,
        "dns_label_count": label_counts,
        "dns_label_avg_len": label_avg_lens,
        "dns_label_max_len": label_max_lens,
        "dns_digit_count": digit_counts,
        "dns_special_char_count": special_counts,
    }


def _extract_temporal(timestamps: list[datetime | None]) -> dict[str, list[int | float | None]]:
    seconds = [_datetime_to_epoch_seconds(value) for value in timestamps]
    window_counts: Counter[int | None] = Counter(
        None if second is None else math.floor(second / 60) for second in seconds
    )
    intervals: list[float | None] = []
    previous: float | None = None
    for second in seconds:
        if second is None or previous is None:
            intervals.append(None)
        else:
            intervals.append(max(0.0, second - previous))
        if second is not None:
            previous = second
    numeric_intervals = [value for value in intervals if value is not None]
    interval_mean = sum(numeric_intervals) / len(numeric_intervals) if numeric_intervals else None
    interval_std = pstdev(numeric_intervals) if len(numeric_intervals) > 1 else 0.0 if numeric_intervals else None
    return {
        "dns_queries_per_window": [
            int(window_counts[None if second is None else math.floor(second / 60)])
            for second in seconds
        ],
        "dns_inter_query_interval_mean": [interval_mean] * len(seconds),
        "dns_inter_query_interval_std": [interval_std] * len(seconds),
        "dns_burst_score": [
            0.0 if interval is None else 1.0 / (1.0 + interval)
            for interval in intervals
        ],
    }


def _domain_values(table: pa.Table) -> list[str]:
    for column in DNS_SOURCE_CANDIDATES:
        if column in table.column_names:
            values = table.column(column).to_pylist()
            return ["" if value is None else str(value).strip().lower() for value in values]
    return [""] * table.num_rows


def _nullable_column(table: pa.Table, column: str, row_count: int) -> list[Any]:
    if column not in table.column_names:
        return [None] * row_count
    return table.column(column).to_pylist()


def _string_column(table: pa.Table, column: str, row_count: int) -> list[str | None]:
    return [None if value is None else str(value) for value in _nullable_column(table, column, row_count)]


def _timestamp_values(table: pa.Table, column: str, row_count: int) -> list[datetime | None]:
    if column not in table.column_names:
        return [None] * row_count
    values = table.column(column).to_pylist()
    return [_coerce_datetime(value) for value in values]


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _datetime_to_epoch_seconds(value: datetime | None) -> float | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def select_existing_required_columns(schema: pa.Schema, requested_columns: tuple[str, ...]) -> list[str]:
    """Keep required column projection compatible with each normalized artifact schema."""
    available = set(schema.names)
    selected = [column for column in requested_columns if column in available]
    if not any(column in available for column in DNS_SOURCE_CANDIDATES):
        raise ValueError(
            "normalized DNS artifact must contain one query/domain column: "
            f"{', '.join(DNS_SOURCE_CANDIDATES)}"
        )
    return selected


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
