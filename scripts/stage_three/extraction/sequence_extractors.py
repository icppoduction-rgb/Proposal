"""Sequence event extraction helpers for Stage Three sequence windows."""

from __future__ import annotations

from typing import Any, Iterable

from scripts.stage_three.labels.label_policy import LABEL_COLUMNS, METADATA_COLUMNS


DEFAULT_SEQUENCE_TRACEABILITY_COLUMNS: tuple[str, ...] = (
    "event_uid",
    "sample_uid",
    "source_file_id",
    "file_id",
    "parser_run_id",
    "normalized_artifact_id",
    "feature_artifact_id",
)

DEFAULT_SEQUENCE_CONTROL_COLUMNS: tuple[str, ...] = (
    "event_timestamp",
    "timestamp",
    "timestamp_type",
    "event_order",
    "host",
    "source_ip",
    "src_ip",
    "user",
    "process",
    "flow_id",
    "sequence_id",
)


def infer_sequence_feature_columns(
    rows: Iterable[dict[str, Any]],
    *,
    explicit_feature_columns: Iterable[str] | None = None,
) -> list[str]:
    """Infer model feature columns for sequence X without labels or traceability."""
    if explicit_feature_columns is not None:
        return [column for column in explicit_feature_columns if str(column).strip()]
    excluded = set(LABEL_COLUMNS)
    excluded.update(METADATA_COLUMNS)
    excluded.update(DEFAULT_SEQUENCE_TRACEABILITY_COLUMNS)
    excluded.update(DEFAULT_SEQUENCE_CONTROL_COLUMNS)
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column in seen or column in excluded or column.startswith("label_"):
                continue
            seen.add(column)
            columns.append(column)
    return columns


def project_sequence_event(
    row: dict[str, Any],
    *,
    feature_columns: Iterable[str],
) -> dict[str, Any]:
    """Return one event with only feature values used in X_sequence."""
    return {column: row.get(column) for column in feature_columns}


def zero_padding_event(feature_columns: Iterable[str]) -> dict[str, Any]:
    """Return one post-padding feature event."""
    return {column: 0 for column in feature_columns}
