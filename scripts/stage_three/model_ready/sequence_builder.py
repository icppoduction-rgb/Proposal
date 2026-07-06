"""Sequence window builder for downstream LSTM/CNN-LSTM training."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from typing import Any, Iterable

import pyarrow as pa

from scripts.stage_three.extraction.sequence_extractors import (
    infer_sequence_feature_columns,
    project_sequence_event,
    zero_padding_event,
)
from scripts.stage_three.labels.label_policy import align_grouped_samples
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK16_REPORT_FILENAME = "Task16-sequence-window-builder.md"
TASK16_PREVIOUS_REPORT_PATH = "Task15-class-balance-report-and-train-only-balancing.md"

DEFAULT_GROUP_BY = ("host", "source_ip", "src_ip", "user", "process", "flow_id")
DEFAULT_SEQUENCE_LENGTH = 50
DEFAULT_STEP = 25
DEFAULT_LABEL_POLICY = "any_attack_in_window"


class SequenceOrderingError(ValueError):
    """Raised when events cannot be ordered without unsafe timestamp synthesis."""


@dataclass(frozen=True)
class SequencePolicy:
    """Policy used to build ordered sequence windows."""

    sequence_length: int = DEFAULT_SEQUENCE_LENGTH
    step: int = DEFAULT_STEP
    padding: str = "post"
    masking_required: bool = True
    label_policy: str = DEFAULT_LABEL_POLICY
    group_by: tuple[str, ...] = DEFAULT_GROUP_BY
    timestamp_column: str = "event_timestamp"
    event_order_column: str = "event_order"
    allow_event_order_fallback: bool = True
    include_partial_windows: bool = True
    feature_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sequence_length <= 0:
            raise ValueError("sequence_length must be positive")
        if self.step <= 0:
            raise ValueError("step must be positive")
        if self.padding != "post":
            raise ValueError("only post-padding is supported")
        if not self.masking_required:
            raise ValueError("masking is required for Stage Three sequences")
        if not self.group_by:
            raise ValueError("at least one group_by column is required")

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly sequence policy metadata."""
        return asdict(self)


@dataclass(frozen=True)
class SequenceWindow:
    """One ordered, padded sequence window."""

    sequence_id: str
    branch: str
    dataset_role: str
    group_key: str
    group_value: str
    sequence_start: Any
    sequence_end: Any
    sequence_length: int
    observed_event_count: int
    padding_count: int
    mask: list[int]
    X_sequence: list[dict[str, Any]]
    y_sequence: dict[str, Any]
    label_policy: str
    traceability_event_uids: list[str]
    ordering_policy: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly sequence metadata."""
        return asdict(self)

    def model_x_row(self) -> dict[str, Any]:
        """Return model input row without labels or traceability_event_uids."""
        return {
            "sequence_id": self.sequence_id,
            "branch": self.branch,
            "dataset_role": self.dataset_role,
            "group_key": self.group_key,
            "group_value": self.group_value,
            "sequence_length": self.sequence_length,
            "padding_count": self.padding_count,
            "mask": list(self.mask),
            "X_sequence": [dict(event) for event in self.X_sequence],
        }

    def traceability_row(self) -> dict[str, Any]:
        """Return traceability outside model X."""
        return {
            "sequence_id": self.sequence_id,
            "traceability_event_uids": list(self.traceability_event_uids),
            "sequence_start": self.sequence_start,
            "sequence_end": self.sequence_end,
            "ordering_policy": self.ordering_policy,
        }


@dataclass(frozen=True)
class SequenceBuildResult:
    """Result of building sequence windows."""

    status: str
    branch: str
    role: str
    policy: SequencePolicy
    windows: list[SequenceWindow]
    padding_statistics: dict[str, Any]
    label_distribution: dict[str, int]
    ordering_policy: str
    timestamp_coverage: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly result metadata."""
        return {
            "status": self.status,
            "branch": self.branch,
            "role": self.role,
            "policy": self.policy.to_dict(),
            "windows": [window.to_dict() for window in self.windows],
            "number_of_sequences": len(self.windows),
            "padding_statistics": dict(self.padding_statistics),
            "label_distribution": dict(self.label_distribution),
            "ordering_policy": self.ordering_policy,
            "timestamp_coverage": dict(self.timestamp_coverage),
            "warnings": list(self.warnings),
            "report_paths": dict(self.report_paths),
        }


def build_sequence_windows(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    branch: str,
    role: str,
    policy: SequencePolicy | None = None,
) -> SequenceBuildResult:
    """Build ordered, padded sequence windows from normalized or feature events."""
    resolved_policy = policy or SequencePolicy()
    input_rows = rows.to_pylist() if isinstance(rows, pa.Table) else [dict(row) for row in rows]
    feature_columns = list(resolved_policy.feature_columns) or infer_sequence_feature_columns(input_rows)
    grouped = _group_rows(input_rows, group_by=resolved_policy.group_by)
    windows: list[SequenceWindow] = []
    ordering_modes: Counter[str] = Counter()
    timestamp_parseable_total = 0
    timestamp_total = len(input_rows)
    warnings: list[str] = []

    for group_key, group_value, group_rows in grouped:
        ordered_rows, ordering_mode, parseable_count = _order_group_rows(group_rows, policy=resolved_policy)
        ordering_modes[ordering_mode] += 1
        timestamp_parseable_total += parseable_count
        for window_index, start in enumerate(_window_starts(len(ordered_rows), resolved_policy)):
            actual_rows = ordered_rows[start : start + resolved_policy.sequence_length]
            if not actual_rows:
                continue
            sequence_id = f"{branch}-{role}-{_safe_id(group_key)}-{_safe_id(group_value)}-{window_index:05d}"
            labeled_rows = [dict(row, sequence_id=sequence_id) for row in actual_rows]
            label_output = align_grouped_samples(
                labeled_rows,
                policy=resolved_policy.label_policy,
                sample_level="sequence",
                group_key="sequence_id",
            )
            y_sequence = label_output.y_rows[0] if label_output.y_rows else _unlabeled_y(sequence_id)
            observed_count = len(actual_rows)
            padding_count = resolved_policy.sequence_length - observed_count
            X_sequence = [project_sequence_event(row, feature_columns=feature_columns) for row in actual_rows]
            X_sequence.extend(zero_padding_event(feature_columns) for _ in range(padding_count))
            mask = [1] * observed_count + [0] * padding_count
            windows.append(
                SequenceWindow(
                    sequence_id=sequence_id,
                    branch=branch,
                    dataset_role=role,
                    group_key=group_key,
                    group_value=group_value,
                    sequence_start=_sequence_boundary(actual_rows[0], ordering_mode, resolved_policy),
                    sequence_end=_sequence_boundary(actual_rows[-1], ordering_mode, resolved_policy),
                    sequence_length=resolved_policy.sequence_length,
                    observed_event_count=observed_count,
                    padding_count=padding_count,
                    mask=mask,
                    X_sequence=X_sequence,
                    y_sequence=y_sequence,
                    label_policy=resolved_policy.label_policy,
                    traceability_event_uids=_event_uids(actual_rows),
                    ordering_policy=ordering_mode,
                )
            )

    if not windows:
        warnings.append("no sequence windows were produced")
    timestamp_coverage = {
        "rows_total": timestamp_total,
        "timestamp_parseable_rows": timestamp_parseable_total,
        "timestamp_coverage": timestamp_parseable_total / timestamp_total if timestamp_total else 0.0,
        "uses_current_runtime_time": False,
    }
    return SequenceBuildResult(
        status="SUCCESS",
        branch=branch,
        role=role,
        policy=resolved_policy,
        windows=windows,
        padding_statistics=_padding_statistics(windows),
        label_distribution=_label_distribution(windows),
        ordering_policy=", ".join(f"{mode}:{count}" for mode, count in sorted(ordering_modes.items())) or "none",
        timestamp_coverage=timestamp_coverage,
        warnings=warnings,
    )


def sequence_windows_to_tables(result: SequenceBuildResult) -> dict[str, list[dict[str, Any]]]:
    """Split sequence windows into X, y, metadata, and traceability rows."""
    return {
        "X": [window.model_x_row() for window in result.windows],
        "y": [dict(window.y_sequence) for window in result.windows],
        "metadata": [
            {
                "sequence_id": window.sequence_id,
                "branch": window.branch,
                "dataset_role": window.dataset_role,
                "group_key": window.group_key,
                "group_value": window.group_value,
                "label_policy": window.label_policy,
                "padding_count": window.padding_count,
                "observed_event_count": window.observed_event_count,
            }
            for window in result.windows
        ],
        "traceability": [window.traceability_row() for window in result.windows],
    }


def save_sequence_builder_reports(result: SequenceBuildResult) -> SequenceBuildResult:
    """Write RU and EN Task16 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK16_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _group_rows(
    rows: list[dict[str, Any]],
    *,
    group_by: tuple[str, ...],
) -> list[tuple[str, str, list[dict[str, Any]]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        group_key, group_value = _group_value(row, group_by=group_by, fallback_index=index)
        grouped[(group_key, group_value)].append(row)
    return [(key, value, grouped[(key, value)]) for key, value in sorted(grouped)]


def _group_value(
    row: dict[str, Any],
    *,
    group_by: tuple[str, ...],
    fallback_index: int,
) -> tuple[str, str]:
    for column in group_by:
        value = row.get(column)
        if value is not None and str(value).strip():
            return column, str(value)
    return "missing_group", f"missing-group-{fallback_index}"


def _order_group_rows(
    rows: list[dict[str, Any]],
    *,
    policy: SequencePolicy,
) -> tuple[list[dict[str, Any]], str, int]:
    timestamp_values = [_parse_timestamp(row.get(policy.timestamp_column)) for row in rows]
    parseable_count = sum(1 for value in timestamp_values if value is not None)
    if parseable_count == len(rows) and rows:
        return (
            [
                row
                for _, row in sorted(
                    zip(timestamp_values, rows),
                    key=lambda item: (item[0], _stable_event_id(item[1])),
                )
            ],
            "timestamp",
            parseable_count,
        )
    if policy.allow_event_order_fallback and _event_order_reliable(rows, policy.event_order_column):
        return (
            sorted(rows, key=lambda row: (_event_order_value(row.get(policy.event_order_column)), _stable_event_id(row))),
            "event_order",
            parseable_count,
        )
    raise SequenceOrderingError(
        "cannot build sequence windows: timestamp coverage is incomplete and event_order is not reliable"
    )


def _window_starts(row_count: int, policy: SequencePolicy) -> list[int]:
    if row_count <= 0:
        return []
    starts = list(range(0, row_count, policy.step))
    if not policy.include_partial_windows:
        starts = [start for start in starts if start + policy.sequence_length <= row_count]
    return starts


def _event_order_reliable(rows: list[dict[str, Any]], column: str) -> bool:
    values = [_event_order_value(row.get(column)) for row in rows]
    return all(value is not None for value in values) and len(set(values)) == len(values)


def _event_order_value(value: Any) -> int | float | str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _sequence_boundary(row: dict[str, Any], ordering_mode: str, policy: SequencePolicy) -> Any:
    if ordering_mode == "timestamp":
        return row.get(policy.timestamp_column)
    return row.get(policy.event_order_column)


def _event_uids(rows: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for index, row in enumerate(rows):
        value = row.get("event_uid", row.get("sample_uid"))
        values.append(str(value) if value is not None and str(value).strip() else f"missing-event-{index}")
    return values


def _stable_event_id(row: dict[str, Any]) -> str:
    value = row.get("event_uid", row.get("sample_uid", ""))
    return str(value)


def _safe_id(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    return safe or "unknown"


def _unlabeled_y(sequence_id: str) -> dict[str, Any]:
    return {
        "sample_uid": sequence_id,
        "label_binary": None,
        "label_family": None,
        "label_subtype": None,
        "label_source": "none",
        "label_status": "unlabeled",
        "label_confidence": None,
        "label_mapping_rule_id": None,
    }


def _padding_statistics(windows: list[SequenceWindow]) -> dict[str, Any]:
    if not windows:
        return {
            "total_padding_count": 0,
            "min_padding_count": 0,
            "max_padding_count": 0,
            "avg_padding_count": 0.0,
            "windows_with_padding": 0,
        }
    padding_counts = [window.padding_count for window in windows]
    return {
        "total_padding_count": sum(padding_counts),
        "min_padding_count": min(padding_counts),
        "max_padding_count": max(padding_counts),
        "avg_padding_count": sum(padding_counts) / len(padding_counts),
        "windows_with_padding": sum(1 for count in padding_counts if count > 0),
    }


def _label_distribution(windows: list[SequenceWindow]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for window in windows:
        label = window.y_sequence.get("label_binary")
        counter["unlabeled" if label is None else str(label)] += 1
    return dict(sorted(counter.items()))


def _render_ru(payload: dict[str, Any]) -> str:
    return _render(payload)


def _render_en(payload: dict[str, Any]) -> str:
    return _render(payload)


def _render(payload: dict[str, Any]) -> str:
    return (
        "# Task 16 - sequence-window-builder\n\n"
        f"- Previous report path: `{TASK16_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Number of sequences: `{payload['number_of_sequences']}`\n"
        f"- Ordering policy: `{payload['ordering_policy']}`\n\n"
        "## Sequence Policy\n\n"
        f"```json\n{_json(payload['policy'])}\n```\n\n"
        "## Padding Statistics\n\n"
        f"```json\n{_json(payload['padding_statistics'])}\n```\n\n"
        "## Label Distribution\n\n"
        f"```json\n{_json(payload['label_distribution'])}\n```\n\n"
        "## Ordering and Timestamp Coverage\n\n"
        f"```json\n{_json(payload['timestamp_coverage'])}\n```\n\n"
        "## Traceability\n\n"
        "- `traceability_event_uids` is stored outside model X in sequence traceability rows.\n"
        "- Missing timestamps are not replaced with current runtime time.\n\n"
        "## Warnings\n\n"
        f"{_warnings(payload['warnings'])}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "branch",
            "role",
            "policy",
            "number_of_sequences",
            "padding_statistics",
            "label_distribution",
            "ordering_policy",
            "timestamp_coverage",
            "warnings",
            "report_paths",
        }
    }


def _warnings(warnings: list[str]) -> str:
    if not warnings:
        return "- `none`"
    return "\n".join(f"- `{warning}`" for warning in warnings)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
