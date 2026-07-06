"""Deterministic label alignment policies for Stage Three samples."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS


LABEL_ALIGNMENT_POLICIES: tuple[str, ...] = (
    "explicit_only",
    "any_attack_in_window",
    "majority_label",
    "last_event_label",
    "weak_allowed_with_confidence",
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

METADATA_COLUMNS: tuple[str, ...] = (
    "sample_uid",
    "event_uid",
    "window_id",
    "flow_id",
    "sequence_id",
    "dataset_id",
    "dataset_name",
    "dataset_role",
    "role",
    "branch",
    "feature_group",
    "source_format",
    "normalized_artifact_id",
    "parser_run_id",
    "source_normalized_path",
)

UNLABELED_STATUS = "unlabeled"
CONFLICTING_STATUS = "conflicting"


@dataclass(frozen=True)
class LabelRecord:
    """Canonical label values extracted from one event/sample row."""

    event_uid: str | None
    event_order: int | float | str | None
    label_binary: int | None
    label_family: str | None
    label_subtype: str | None
    label_source: str
    label_status: str
    label_confidence: float | None
    label_mapping_rule_id: str | None

    @property
    def has_label(self) -> bool:
        return self.label_binary is not None or self.label_family is not None or self.label_subtype is not None


@dataclass(frozen=True)
class LabelDecision:
    """Aligned label for one output sample."""

    sample_uid: str
    sample_level: str
    policy: str
    label_binary: int | None
    label_family: str | None
    label_subtype: str | None
    label_source: str
    label_status: str
    label_confidence: float | None
    label_mapping_rule_id: str | None
    source_event_uids: list[str] = field(default_factory=list)
    contributing_label_count: int = 0
    unlabeled_event_count: int = 0
    conflicting: bool = False
    conflict_values: list[int] = field(default_factory=list)

    def y_row(self) -> dict[str, Any]:
        """Return target/y fields without model input features."""
        return {
            "sample_uid": self.sample_uid,
            "label_binary": self.label_binary,
            "label_family": self.label_family,
            "label_subtype": self.label_subtype,
            "label_source": self.label_source,
            "label_status": self.label_status,
            "label_confidence": self.label_confidence,
            "label_mapping_rule_id": self.label_mapping_rule_id,
        }

    def metadata_row(self) -> dict[str, Any]:
        """Return label audit metadata separated from X."""
        return {
            "sample_uid": self.sample_uid,
            "sample_level": self.sample_level,
            "label_policy": self.policy,
            "label_source": self.label_source,
            "label_status": self.label_status,
            "label_confidence": self.label_confidence,
            "label_mapping_rule_id": self.label_mapping_rule_id,
            "source_event_uids": list(self.source_event_uids),
            "contributing_label_count": self.contributing_label_count,
            "unlabeled_event_count": self.unlabeled_event_count,
            "conflicting": self.conflicting,
            "conflict_values": list(self.conflict_values),
        }

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        return asdict(self)


@dataclass(frozen=True)
class LabelAlignmentOutput:
    """Separated X/y/metadata output produced by label alignment."""

    policy: str
    sample_level: str
    x_rows: list[dict[str, Any]]
    y_rows: list[dict[str, Any]]
    metadata_rows: list[dict[str, Any]]
    decisions: list[LabelDecision]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        return {
            "policy": self.policy,
            "sample_level": self.sample_level,
            "x_rows": self.x_rows,
            "y_rows": self.y_rows,
            "metadata_rows": self.metadata_rows,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "summary": self.summary,
        }


def align_samples(
    rows: list[dict[str, Any]],
    *,
    policy: str,
    sample_level: str = "event",
    group_key: str | None = None,
    sample_uid_key: str = "sample_uid",
    min_weak_confidence: float = 0.0,
) -> LabelAlignmentOutput:
    """Align labels for event samples or grouped window/flow/sequence samples."""
    validate_label_policy(policy)
    if group_key is None:
        return align_event_samples(
            rows,
            policy=policy,
            sample_level=sample_level,
            sample_uid_key=sample_uid_key,
            min_weak_confidence=min_weak_confidence,
        )
    return align_grouped_samples(
        rows,
        policy=policy,
        sample_level=sample_level,
        group_key=group_key,
        min_weak_confidence=min_weak_confidence,
    )


def align_event_samples(
    rows: list[dict[str, Any]],
    *,
    policy: str,
    sample_level: str = "event",
    sample_uid_key: str = "sample_uid",
    min_weak_confidence: float = 0.0,
) -> LabelAlignmentOutput:
    """Align labels one row at a time and keep y/metadata separate from X."""
    validate_label_policy(policy)
    decisions: list[LabelDecision] = []
    x_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        sample_uid = _sample_uid(row, sample_uid_key=sample_uid_key, fallback_index=index)
        decision = decide_label(
            [_label_record(row)],
            policy=policy,
            sample_uid=sample_uid,
            sample_level=sample_level,
            min_weak_confidence=min_weak_confidence,
        )
        decisions.append(decision)
        x_rows.append(strip_x_forbidden_columns(row))
        metadata_rows.append({**_metadata_from_row(row), **decision.metadata_row()})
    y_rows = [decision.y_row() for decision in decisions]
    return LabelAlignmentOutput(
        policy=policy,
        sample_level=sample_level,
        x_rows=x_rows,
        y_rows=y_rows,
        metadata_rows=metadata_rows,
        decisions=decisions,
        summary=summarize_label_alignment(decisions),
    )


def align_grouped_samples(
    rows: list[dict[str, Any]],
    *,
    policy: str,
    sample_level: str,
    group_key: str,
    min_weak_confidence: float = 0.0,
) -> LabelAlignmentOutput:
    """Align labels for grouped samples such as windows, flows, or sequences."""
    validate_label_policy(policy)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        group_value = row.get(group_key)
        if group_value is None or str(group_value).strip() == "":
            group_value = f"missing-{group_key}-{index}"
        grouped[str(group_value)].append(row)

    x_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    decisions: list[LabelDecision] = []
    for group_id in sorted(grouped):
        group_rows = _sort_rows_deterministically(grouped[group_id])
        records = [_label_record(row) for row in group_rows]
        decision = decide_label(
            records,
            policy=policy,
            sample_uid=group_id,
            sample_level=sample_level,
            min_weak_confidence=min_weak_confidence,
        )
        decisions.append(decision)
        x_rows.append(_group_x_row(group_id=group_id, group_key=group_key, rows=group_rows))
        metadata_rows.append(
            {
                **_metadata_from_row(group_rows[0]),
                group_key: group_id,
                **decision.metadata_row(),
            }
        )
    y_rows = [decision.y_row() for decision in decisions]
    return LabelAlignmentOutput(
        policy=policy,
        sample_level=sample_level,
        x_rows=x_rows,
        y_rows=y_rows,
        metadata_rows=metadata_rows,
        decisions=decisions,
        summary=summarize_label_alignment(decisions),
    )


def decide_label(
    records: list[LabelRecord],
    *,
    policy: str,
    sample_uid: str,
    sample_level: str,
    min_weak_confidence: float = 0.0,
) -> LabelDecision:
    """Apply one label policy to canonical event label records."""
    validate_label_policy(policy)
    ordered = sorted(records, key=_record_sort_key)
    source_event_uids = [record.event_uid for record in ordered if record.event_uid]
    eligible = [
        record
        for record in ordered
        if _record_allowed_by_policy(record, policy=policy, min_weak_confidence=min_weak_confidence)
    ]
    unlabeled_event_count = len([record for record in ordered if not record.has_label])
    if not eligible:
        return _unlabeled_decision(
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            unlabeled_event_count=len(ordered),
        )

    if policy in {"explicit_only", "weak_allowed_with_confidence"} and len(eligible) == 1:
        return _decision_from_record(
            eligible[0],
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            contributing_label_count=1,
            unlabeled_event_count=unlabeled_event_count,
        )

    if policy == "last_event_label":
        return _decision_from_record(
            eligible[-1],
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            contributing_label_count=len(eligible),
            unlabeled_event_count=unlabeled_event_count,
            conflict_values=_conflict_values(eligible),
        )

    if policy == "majority_label":
        return _majority_decision(
            eligible,
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            unlabeled_event_count=unlabeled_event_count,
        )

    if policy == "any_attack_in_window":
        return _any_attack_decision(
            eligible,
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            unlabeled_event_count=unlabeled_event_count,
        )

    return _majority_decision(
        eligible,
        sample_uid=sample_uid,
        sample_level=sample_level,
        policy=policy,
        source_event_uids=source_event_uids,
        unlabeled_event_count=unlabeled_event_count,
    )


def strip_x_forbidden_columns(row: dict[str, Any]) -> dict[str, Any]:
    """Return an X row without label/source/leakage columns."""
    forbidden = set(FORBIDDEN_X_COLUMNS)
    forbidden.update(LABEL_COLUMNS)
    return {key: value for key, value in row.items() if key not in forbidden and not key.startswith("label_")}


def summarize_label_alignment(decisions: list[LabelDecision]) -> dict[str, Any]:
    """Return coverage and distribution metrics for aligned labels."""
    total = len(decisions)
    labeled = len([decision for decision in decisions if decision.label_binary is not None])
    unlabeled = len([decision for decision in decisions if decision.label_status == UNLABELED_STATUS])
    conflicting = len([decision for decision in decisions if decision.conflicting])
    status_counts = Counter(decision.label_status for decision in decisions)
    source_counts = Counter(decision.label_source for decision in decisions)
    binary_counts = Counter(
        "unlabeled" if decision.label_binary is None else str(decision.label_binary)
        for decision in decisions
    )
    return {
        "sample_count": total,
        "labeled_count": labeled,
        "label_coverage": labeled / total if total else 0.0,
        "unlabeled_count": unlabeled,
        "conflicting_count": conflicting,
        "label_status_distribution": dict(sorted(status_counts.items())),
        "label_source_distribution": dict(sorted(source_counts.items())),
        "label_binary_distribution": dict(sorted(binary_counts.items())),
    }


def validate_label_policy(policy: str) -> None:
    """Raise ValueError for unsupported label policies."""
    if policy not in LABEL_ALIGNMENT_POLICIES:
        allowed = ", ".join(LABEL_ALIGNMENT_POLICIES)
        raise ValueError(f"unsupported label policy={policy!r}; allowed values: {allowed}")


def _label_record(row: dict[str, Any]) -> LabelRecord:
    status = _clean_text(row.get("label_status")) or UNLABELED_STATUS
    source = _clean_text(row.get("label_source")) or "none"
    binary = _normalize_binary(row.get("label_binary"))
    family = _clean_text(row.get("label_family"))
    subtype = _clean_text(row.get("label_subtype"))
    if binary is None and family is None and subtype is None:
        status = UNLABELED_STATUS
        source = "none" if source == "" else source
    return LabelRecord(
        event_uid=_clean_text(row.get("event_uid")) or _clean_text(row.get("sample_uid")),
        event_order=row.get("event_order", row.get("event_index")),
        label_binary=binary,
        label_family=family,
        label_subtype=subtype,
        label_source=source,
        label_status=status,
        label_confidence=_normalize_confidence(row.get("label_confidence")),
        label_mapping_rule_id=_clean_text(row.get("label_mapping_rule_id")),
    )


def _record_allowed_by_policy(
    record: LabelRecord,
    *,
    policy: str,
    min_weak_confidence: float,
) -> bool:
    if not record.has_label:
        return False
    if policy == "weak_allowed_with_confidence":
        if _is_weak(record):
            return record.label_confidence is not None and record.label_confidence >= min_weak_confidence
        return _is_explicit(record)
    return _is_explicit(record)


def _is_explicit(record: LabelRecord) -> bool:
    status = record.label_status.lower()
    if status in {UNLABELED_STATUS, "missing", "none"}:
        return False
    if "weak" in status:
        return False
    if status in {"explicit", "explicit_label", "verified", "ground_truth", "manual"}:
        return True
    return record.has_label and record.label_source.lower() not in {"none", "weak", "filename_hint"}


def _is_weak(record: LabelRecord) -> bool:
    return "weak" in record.label_status.lower() or record.label_source.lower() == "weak"


def _unlabeled_decision(
    *,
    sample_uid: str,
    sample_level: str,
    policy: str,
    source_event_uids: list[str],
    unlabeled_event_count: int,
) -> LabelDecision:
    return LabelDecision(
        sample_uid=sample_uid,
        sample_level=sample_level,
        policy=policy,
        label_binary=None,
        label_family=None,
        label_subtype=None,
        label_source="none",
        label_status=UNLABELED_STATUS,
        label_confidence=None,
        label_mapping_rule_id=None,
        source_event_uids=source_event_uids,
        contributing_label_count=0,
        unlabeled_event_count=unlabeled_event_count,
    )


def _decision_from_record(
    record: LabelRecord,
    *,
    sample_uid: str,
    sample_level: str,
    policy: str,
    source_event_uids: list[str],
    contributing_label_count: int,
    unlabeled_event_count: int,
    conflict_values: list[int] | None = None,
) -> LabelDecision:
    conflicts = conflict_values or []
    return LabelDecision(
        sample_uid=sample_uid,
        sample_level=sample_level,
        policy=policy,
        label_binary=record.label_binary,
        label_family=record.label_family,
        label_subtype=record.label_subtype,
        label_source=record.label_source,
        label_status=CONFLICTING_STATUS if conflicts else record.label_status,
        label_confidence=record.label_confidence,
        label_mapping_rule_id=record.label_mapping_rule_id,
        source_event_uids=source_event_uids,
        contributing_label_count=contributing_label_count,
        unlabeled_event_count=unlabeled_event_count,
        conflicting=bool(conflicts),
        conflict_values=conflicts,
    )


def _majority_decision(
    records: list[LabelRecord],
    *,
    sample_uid: str,
    sample_level: str,
    policy: str,
    source_event_uids: list[str],
    unlabeled_event_count: int,
) -> LabelDecision:
    binary_records = [record for record in records if record.label_binary is not None]
    counts = Counter(record.label_binary for record in binary_records)
    if not counts:
        return _unlabeled_decision(
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            unlabeled_event_count=unlabeled_event_count,
        )
    most_common = counts.most_common()
    if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
        return _conflicting_decision(
            records,
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            unlabeled_event_count=unlabeled_event_count,
            label_binary=None,
        )
    selected_value = most_common[0][0]
    selected_record = next(record for record in binary_records if record.label_binary == selected_value)
    return _decision_from_record(
        selected_record,
        sample_uid=sample_uid,
        sample_level=sample_level,
        policy=policy,
        source_event_uids=source_event_uids,
        contributing_label_count=len(binary_records),
        unlabeled_event_count=unlabeled_event_count,
        conflict_values=_conflict_values(binary_records),
    )


def _any_attack_decision(
    records: list[LabelRecord],
    *,
    sample_uid: str,
    sample_level: str,
    policy: str,
    source_event_uids: list[str],
    unlabeled_event_count: int,
) -> LabelDecision:
    binary_records = [record for record in records if record.label_binary is not None]
    if not binary_records:
        return _unlabeled_decision(
            sample_uid=sample_uid,
            sample_level=sample_level,
            policy=policy,
            source_event_uids=source_event_uids,
            unlabeled_event_count=unlabeled_event_count,
        )
    selected_value = 1 if any(record.label_binary == 1 for record in binary_records) else 0
    selected_record = next(record for record in binary_records if record.label_binary == selected_value)
    return _decision_from_record(
        selected_record,
        sample_uid=sample_uid,
        sample_level=sample_level,
        policy=policy,
        source_event_uids=source_event_uids,
        contributing_label_count=len(binary_records),
        unlabeled_event_count=unlabeled_event_count,
        conflict_values=_conflict_values(binary_records),
    )


def _conflicting_decision(
    records: list[LabelRecord],
    *,
    sample_uid: str,
    sample_level: str,
    policy: str,
    source_event_uids: list[str],
    unlabeled_event_count: int,
    label_binary: int | None,
) -> LabelDecision:
    first = records[0]
    return LabelDecision(
        sample_uid=sample_uid,
        sample_level=sample_level,
        policy=policy,
        label_binary=label_binary,
        label_family=first.label_family,
        label_subtype=first.label_subtype,
        label_source=first.label_source,
        label_status=CONFLICTING_STATUS,
        label_confidence=first.label_confidence,
        label_mapping_rule_id=first.label_mapping_rule_id,
        source_event_uids=source_event_uids,
        contributing_label_count=len([record for record in records if record.label_binary is not None]),
        unlabeled_event_count=unlabeled_event_count,
        conflicting=True,
        conflict_values=_conflict_values(records),
    )


def _conflict_values(records: list[LabelRecord]) -> list[int]:
    values = sorted({int(record.label_binary) for record in records if record.label_binary is not None})
    return values if len(values) > 1 else []


def _metadata_from_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for column in METADATA_COLUMNS:
        if column in row:
            metadata[column] = row[column]
    for column in LABEL_COLUMNS[3:]:
        if column in row:
            metadata[column] = row[column]
    return metadata


def _group_x_row(*, group_id: str, group_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    base: dict[str, Any] = {group_key: group_id, "sample_count": len(rows)}
    for key, value in strip_x_forbidden_columns(rows[0]).items():
        if key not in {group_key, "event_order", "event_index", "event_uid", "sample_uid"}:
            base[key] = value
    return base


def _sort_rows_deterministically(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            _sortable_value(row.get("event_order", row.get("event_index"))),
            str(row.get("event_uid", row.get("sample_uid", ""))),
        ),
    )


def _record_sort_key(record: LabelRecord) -> tuple[Any, str]:
    return (_sortable_value(record.event_order), str(record.event_uid or ""))


def _sortable_value(value: Any) -> tuple[int, Any]:
    if value is None:
        return (1, "")
    if isinstance(value, (int, float)):
        return (0, value)
    text = str(value)
    try:
        return (0, float(text))
    except ValueError:
        return (0, text)


def _sample_uid(row: dict[str, Any], *, sample_uid_key: str, fallback_index: int) -> str:
    for key in (sample_uid_key, "sample_uid", "event_uid"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return f"sample-{fallback_index}"


def _normalize_binary(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in {0, 1}:
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "attack", "malicious", "exfiltration"}:
        return 1
    if text in {"0", "false", "benign", "normal"}:
        return 0
    return None


def _normalize_confidence(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
