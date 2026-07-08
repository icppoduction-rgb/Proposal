"""Core Host feature extractors for Stage Three normalized artifacts."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pyarrow as pa

from scripts.stage_three.extraction.common import (
    BASE_NORMALIZED_COLUMNS,
    LABEL_COLUMNS,
    TRACEABILITY_COLUMNS,
    first_value,
    json_rows,
    labels_payload,
    missing_ratios,
    nullable_values,
    select_existing_columns,
    stable_hash_int,
    string_values,
    traceability_payload,
)


HOST_FEATURE_GROUPS: tuple[str, ...] = (
    "host_syscall",
    "host_process",
    "host_auth",
    "host_file_access",
    "host_metrics",
    "host_logs",
)
HOST_FEATURES: dict[str, tuple[str, ...]] = {
    "host_syscall": ("host_syscall_frequency_vector",),
    "host_process": ("host_process_name_hash",),
    "host_auth": ("host_auth_failure_flag",),
    "host_file_access": ("host_file_access_count",),
    "host_metrics": ("host_cpu_load_pct",),
    "host_logs": ("host_log_severity",),
}
HOST_SOURCE_COLUMNS: tuple[str, ...] = (
    *BASE_NORMALIZED_COLUMNS,
    "host",
    "host_name",
    "user",
    "user_name",
    "process",
    "process_id",
    "process_name",
    "parent_process_id",
    "parent_process_name",
    "syscall_name",
    "event_id",
    "command_line",
    "file_path",
    "metric_name",
    "metric_value",
)
SYSCALL_VECTOR_BUCKETS = 16
SEVERITY_CODES = {
    "debug": 0,
    "trace": 0,
    "info": 1,
    "information": 1,
    "notice": 1,
    "warn": 2,
    "warning": 2,
    "err": 3,
    "error": 3,
    "fail": 3,
    "failed": 3,
    "critical": 4,
    "crit": 4,
    "fatal": 4,
    "alert": 4,
    "emergency": 4,
}
_HOST_COLUMN_CACHE_KEYS: tuple[str, ...] = (
    "event_type",
    "raw_event_name",
    "source_format",
    "syscall_name",
    "process_name",
    "process",
    "process_id",
    "file_path",
    "metric_value",
    "metric_name",
)


def host_feature_columns(feature_group: str) -> tuple[str, ...]:
    """Return feature columns produced for a Host feature group."""
    try:
        return HOST_FEATURES[feature_group]
    except KeyError as exc:
        allowed = ", ".join(HOST_FEATURE_GROUPS)
        raise ValueError(f"unsupported Host feature_group={feature_group!r}; allowed: {allowed}") from exc


def required_host_columns(feature_group: str) -> tuple[str, ...]:
    """Return normalized input columns needed for a Host extractor."""
    host_feature_columns(feature_group)
    return HOST_SOURCE_COLUMNS


def select_existing_required_columns(schema: pa.Schema, requested_columns: tuple[str, ...]) -> list[str]:
    """Keep Host projection compatible with each normalized artifact schema."""
    selected = select_existing_columns(schema, requested_columns)
    if not selected:
        raise ValueError("normalized Host artifact does not contain any supported normalized-event columns")
    return selected


def extract_host_features_from_table(
    table: pa.Table,
    *,
    feature_group: str,
    normalized_artifact_id: int,
    dataset_id: int,
    role: str,
    source_normalized_path: str,
) -> pa.Table:
    """Extract core Host features for one bounded Arrow table."""
    feature_columns = host_feature_columns(feature_group)
    payload: dict[str, Any] = traceability_payload(
        table=table,
        normalized_artifact_id=normalized_artifact_id,
        dataset_id=dataset_id,
        role=role,
        branch="host",
        feature_group=feature_group,
        source_normalized_path=source_normalized_path,
    )
    context = _HostContext.from_table(table)
    if feature_group == "host_syscall":
        payload.update({"host_syscall_frequency_vector": _syscall_vectors(context)})
    elif feature_group == "host_process":
        payload.update({"host_process_name_hash": _process_hashes(context)})
    elif feature_group == "host_auth":
        payload.update({"host_auth_failure_flag": _auth_failure_flags(context)})
    elif feature_group == "host_file_access":
        payload.update({"host_file_access_count": _file_access_counts(context)})
    elif feature_group == "host_metrics":
        payload.update({"host_cpu_load_pct": _cpu_load_pct(context)})
    elif feature_group == "host_logs":
        payload.update({"host_log_severity": _log_severity_codes(context)})
    payload.update(labels_payload(table))
    ordered = {
        **{column: payload[column] for column in TRACEABILITY_COLUMNS},
        **{column: payload[column] for column in feature_columns},
        **{column: payload[column] for column in LABEL_COLUMNS},
    }
    return pa.table(ordered)


class _HostContext:
    """Column and JSON payload view for one Host extraction batch."""

    def __init__(
        self,
        *,
        table: pa.Table,
        features_rows: list[dict[str, Any]],
        raw_rows: list[dict[str, Any]],
        metadata_rows: list[dict[str, Any]],
    ) -> None:
        self.table = table
        self.features_rows = features_rows
        self.raw_rows = raw_rows
        self.metadata_rows = metadata_rows
        self._columns: dict[str, list[Any]] = self._build_column_cache(table)
        self._missing_columns: list[Any] = [None] * table.num_rows
        self.event_types = self._string_values("event_type")
        self.raw_event_names = self._string_values("raw_event_name")
        self.source_formats = self._string_values("source_format")

    @classmethod
    def from_table(cls, table: pa.Table) -> "_HostContext":
        return cls(
            table=table,
            features_rows=json_rows(table, "features_json"),
            raw_rows=json_rows(table, "raw_fields_json"),
            metadata_rows=json_rows(table, "metadata_json"),
        )

    @staticmethod
    def _build_column_cache(table: pa.Table) -> dict[str, list[Any]]:
        requested = {column for column in table.column_names if column in _HOST_COLUMN_CACHE_KEYS}
        return {column: nullable_values(table, column) for column in requested}

    def _column_values(self, column: str) -> list[Any]:
        return self._columns.get(column, self._missing_columns)

    def _string_values(self, column: str) -> list[str | None]:
        return [
            None if value is None else str(value).strip()
            for value in self._column_values(column)
        ]

    def column_or_payload(self, row_index: int, columns: tuple[str, ...], payload_keys: tuple[str, ...]) -> Any:
        for column in columns:
            value = self._column_values(column)[row_index]
            if value not in (None, ""):
                return value
        for source in (self.features_rows[row_index], self.raw_rows[row_index], self.metadata_rows[row_index]):
            value = first_value(source, payload_keys)
            if value not in (None, ""):
                return value
        return None


def _syscall_vectors(context: _HostContext) -> list[list[float]]:
    bucket_counts: Counter[int] = Counter()
    row_buckets: list[int | None] = []
    for index in range(context.table.num_rows):
        name = _syscall_name(context, index)
        bucket = stable_hash_int(name, modulo=SYSCALL_VECTOR_BUCKETS)
        row_buckets.append(bucket)
        if bucket is not None:
            bucket_counts[bucket] += 1
    denominator = max(1, sum(bucket_counts.values()))
    vectors: list[list[float]] = []
    for bucket in row_buckets:
        vector = [0.0] * SYSCALL_VECTOR_BUCKETS
        if bucket is not None:
            vector[bucket] = bucket_counts[bucket] / denominator
        vectors.append(vector)
    return vectors


def _syscall_name(context: _HostContext, index: int) -> str | None:
    value = context.column_or_payload(
        index,
        columns=("syscall_name", "raw_event_name", "event_type"),
        payload_keys=("syscall_name", "syscall", "MethodName", "method_name", "event.action", "operation"),
    )
    return None if value in (None, "") else str(value)


def _process_hashes(context: _HostContext) -> list[int | None]:
    hashes: list[int | None] = []
    for index in range(context.table.num_rows):
        value = context.column_or_payload(
            index,
            columns=("process_name", "process", "process_id"),
            payload_keys=("process_name", "process.name", "ProcessName", "process", "Image", "CommandLine"),
        )
        hashes.append(stable_hash_int(value, modulo=1_000_003))
    return hashes


def _auth_failure_flags(context: _HostContext) -> list[int]:
    flags: list[int] = []
    for index in range(context.table.num_rows):
        values = [
            context.event_types[index],
            context.raw_event_names[index],
            context.column_or_payload(
                index,
                columns=("user_name", "user"),
                payload_keys=("event.outcome", "outcome", "status", "message", "msg"),
            ),
        ]
        text = " ".join(str(value).lower() for value in values if value not in (None, ""))
        flags.append(1 if any(token in text for token in ("fail", "failed", "failure", "invalid", "denied")) else 0)
    return flags


def _file_access_counts(context: _HostContext) -> list[int]:
    counts: list[int] = []
    for index in range(context.table.num_rows):
        path_value = context.column_or_payload(
            index,
            columns=("file_path",),
            payload_keys=("file_path", "file.path", "path", "target_filename", "mapped_arguments.path"),
        )
        event_text = " ".join(
            str(value).lower()
            for value in (context.event_types[index], context.raw_event_names[index])
            if value not in (None, "")
        )
        explicit_count = context.column_or_payload(
            index,
            columns=(),
            payload_keys=("file_access_count", "file.count", "files_touched"),
        )
        if explicit_count not in (None, ""):
            try:
                counts.append(max(0, int(float(explicit_count))))
                continue
            except (TypeError, ValueError):
                pass
        counts.append(1 if path_value not in (None, "") or any(token in event_text for token in _FILE_TOKENS) else 0)
    return counts


_FILE_TOKENS = ("file", "open", "read", "write", "createfile", "delete", "rename")


def _cpu_load_pct(context: _HostContext) -> list[float | None]:
    values: list[float | None] = []
    metric_values = nullable_values(context.table, "metric_value")
    metric_names = string_values(context.table, "metric_name")
    for index in range(context.table.num_rows):
        candidate = None
        metric_name = (metric_names[index] or "").lower()
        if "cpu" in metric_name:
            candidate = metric_values[index]
        if candidate in (None, ""):
            candidate = context.column_or_payload(
                index,
                columns=(),
                payload_keys=(
                    "host_cpu_load_pct",
                    "cpu_pct",
                    "cpu.percent",
                    "system.cpu.total.norm.pct",
                    "system.cpu.total.pct",
                    "cpu",
                ),
            )
        number = _float_or_none(candidate)
        if number is None:
            values.append(None)
        elif 0.0 <= number <= 1.0:
            values.append(number * 100.0)
        else:
            values.append(number)
    return values


def _log_severity_codes(context: _HostContext) -> list[int | None]:
    values: list[int | None] = []
    for index in range(context.table.num_rows):
        severity = context.column_or_payload(
            index,
            columns=(),
            payload_keys=("severity", "log.level", "level", "apache_severity", "alert.severity"),
        )
        text = " ".join(
            str(value).lower()
            for value in (severity, context.event_types[index], context.raw_event_names[index])
            if value not in (None, "")
        )
        values.append(_severity_code(text))
    return values


def _severity_code(text: str) -> int | None:
    if not text:
        return None
    for token, code in SEVERITY_CODES.items():
        if token in text:
            return code
    return 1


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def host_missing_ratios(table: pa.Table, columns: tuple[str, ...]) -> dict[str, float]:
    """Calculate missing ratios for Host feature columns."""
    return missing_ratios(table, columns)
