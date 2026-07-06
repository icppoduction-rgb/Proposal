"""Class balance reporting and TRAIN-only optional balancing for Stage Three."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any


TRAIN_ROLE = "TRAIN"
VALIDATION_ROLE = "VALIDATION"
TEST_ROLE = "TEST"
SPLIT_ROLES = (TRAIN_ROLE, VALIDATION_ROLE, TEST_ROLE)

BALANCING_NONE = "none"
BALANCING_RANDOM_UNDERSAMPLING = "random_undersampling"
BALANCING_RANDOM_OVERSAMPLING = "random_oversampling"
BALANCING_SMOTE = "smote"
BALANCING_METHODS = (
    BALANCING_NONE,
    BALANCING_RANDOM_UNDERSAMPLING,
    BALANCING_RANDOM_OVERSAMPLING,
    BALANCING_SMOTE,
)


class TrainOnlyBalancingError(ValueError):
    """Raised when physical balancing is requested for a non-TRAIN split."""


@dataclass(frozen=True)
class ClassDistribution:
    """Class and label metadata distribution for one split."""

    role: str
    rows_total: int
    labeled_count: int
    missing_label_count: int
    class_counts: dict[str, int]
    class_ratio: dict[str, float]
    label_status_distribution: dict[str, int]
    label_source_distribution: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly distribution metadata."""
        return asdict(self)


@dataclass(frozen=True)
class ClassWeightMetadata:
    """Stage Four class weighting recommendations."""

    class_weight: dict[str, float]
    scale_pos_weight: float | None
    positive_label: str = "1"
    negative_label: str = "0"
    labeled_count: int = 0
    missing_label_count: int = 0
    recommendation: str = "use class_weight for RF/linear baselines and scale_pos_weight for XGBoost"

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly class-weight metadata."""
        return asdict(self)


@dataclass(frozen=True)
class ClassBalanceResult:
    """Result of optional balancing for one split."""

    role: str
    method: str
    rows_before: int
    rows_after: int
    before_distribution: ClassDistribution
    after_distribution: ClassDistribution
    output_rows: list[dict[str, Any]]
    class_weight_metadata: ClassWeightMetadata | None = None
    validation_test_not_modified: bool = True
    physical_resampling_applied: bool = False
    smote_enabled: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly balance result."""
        return {
            "role": self.role,
            "method": self.method,
            "rows_before": self.rows_before,
            "rows_after": self.rows_after,
            "before_distribution": self.before_distribution.to_dict(),
            "after_distribution": self.after_distribution.to_dict(),
            "class_weight_metadata": self.class_weight_metadata.to_dict()
            if self.class_weight_metadata is not None
            else None,
            "validation_test_not_modified": self.validation_test_not_modified,
            "physical_resampling_applied": self.physical_resampling_applied,
            "smote_enabled": self.smote_enabled,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ClassBalanceReportResult:
    """Full TRAIN/VALIDATION/TEST class balance report payload."""

    status: str
    balancing_method: str
    splits: dict[str, ClassBalanceResult]
    class_weight_metadata: ClassWeightMetadata
    validation_test_not_modified: bool
    smote_enabled: bool
    warnings: list[str] = field(default_factory=list)
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly report payload."""
        return {
            "status": self.status,
            "balancing_method": self.balancing_method,
            "splits": {role: result.to_dict() for role, result in self.splits.items()},
            "class_weight_metadata": self.class_weight_metadata.to_dict(),
            "validation_test_not_modified": self.validation_test_not_modified,
            "smote_enabled": self.smote_enabled,
            "warnings": list(self.warnings),
            "report_paths": dict(self.report_paths),
        }


def summarize_class_distribution(
    rows: list[dict[str, Any]],
    *,
    role: str,
    target_column: str = "label_binary",
) -> ClassDistribution:
    """Summarize labels without treating missing labels as benign."""
    normalized_role = _normalize_role(role)
    class_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    missing_labels = 0
    for row in rows:
        label = _normalize_label(row.get(target_column))
        status = _clean_text(row.get("label_status")) or ("unlabeled" if label is None else "unknown")
        source = _clean_text(row.get("label_source")) or ("none" if label is None else "unknown")
        status_counter[status] += 1
        source_counter[source] += 1
        if label is None:
            missing_labels += 1
            continue
        class_counter[label] += 1
    labeled_count = sum(class_counter.values())
    return ClassDistribution(
        role=normalized_role,
        rows_total=len(rows),
        labeled_count=labeled_count,
        missing_label_count=missing_labels,
        class_counts=dict(sorted(class_counter.items())),
        class_ratio={
            label: count / labeled_count if labeled_count else 0.0
            for label, count in sorted(class_counter.items())
        },
        label_status_distribution=dict(sorted(status_counter.items())),
        label_source_distribution=dict(sorted(source_counter.items())),
    )


def compute_class_weight_metadata(distribution: ClassDistribution) -> ClassWeightMetadata:
    """Compute balanced class weights and XGBoost scale_pos_weight metadata."""
    class_counts = distribution.class_counts
    labeled_count = sum(class_counts.values())
    class_count = len(class_counts)
    weights = {
        label: labeled_count / (class_count * count) if class_count and count else 0.0
        for label, count in sorted(class_counts.items())
    }
    negative_count = class_counts.get("0", 0)
    positive_count = class_counts.get("1", 0)
    scale_pos_weight = negative_count / positive_count if positive_count else None
    return ClassWeightMetadata(
        class_weight=weights,
        scale_pos_weight=scale_pos_weight,
        labeled_count=labeled_count,
        missing_label_count=distribution.missing_label_count,
    )


def balance_split(
    rows: list[dict[str, Any]],
    *,
    role: str,
    method: str = BALANCING_NONE,
    target_column: str = "label_binary",
    random_seed: int = 42,
    enable_smote: bool = False,
) -> ClassBalanceResult:
    """Report and optionally balance one split. Physical balancing is TRAIN-only."""
    normalized_role = _normalize_role(role)
    normalized_method = _normalize_method(method)
    if normalized_role != TRAIN_ROLE and (normalized_method != BALANCING_NONE or enable_smote):
        raise TrainOnlyBalancingError("physical class balancing is allowed only on TRAIN")
    if normalized_method == BALANCING_SMOTE and not enable_smote:
        raise ValueError("SMOTE requires enable_smote=True and remains disabled by default")

    before = summarize_class_distribution(rows, role=normalized_role, target_column=target_column)
    warnings = _distribution_warnings(before)
    output_rows = [dict(row) for row in rows]
    physical_applied = False
    smote_enabled = normalized_method == BALANCING_SMOTE and enable_smote

    if normalized_role == TRAIN_ROLE:
        if normalized_method == BALANCING_RANDOM_UNDERSAMPLING:
            output_rows, applied, method_warnings = _random_undersample(
                output_rows,
                target_column=target_column,
                random_seed=random_seed,
            )
            physical_applied = applied
            warnings.extend(method_warnings)
        elif normalized_method == BALANCING_RANDOM_OVERSAMPLING:
            output_rows, applied, method_warnings = _random_oversample(
                output_rows,
                target_column=target_column,
                random_seed=random_seed,
            )
            physical_applied = applied
            warnings.extend(method_warnings)
        elif normalized_method == BALANCING_SMOTE:
            warnings.append(
                "SMOTE was explicitly requested; MVP keeps it disabled as a physical transform and records an ablation warning."
            )

    after = summarize_class_distribution(output_rows, role=normalized_role, target_column=target_column)
    return ClassBalanceResult(
        role=normalized_role,
        method=normalized_method,
        rows_before=len(rows),
        rows_after=len(output_rows),
        before_distribution=before,
        after_distribution=after,
        output_rows=output_rows,
        class_weight_metadata=compute_class_weight_metadata(before)
        if normalized_role == TRAIN_ROLE
        else None,
        validation_test_not_modified=normalized_role in {VALIDATION_ROLE, TEST_ROLE}
        and len(output_rows) == len(rows)
        and output_rows == rows,
        physical_resampling_applied=physical_applied,
        smote_enabled=smote_enabled,
        warnings=warnings,
    )


def build_class_balance_report(
    split_rows: dict[str, list[dict[str, Any]]],
    *,
    train_method: str = BALANCING_NONE,
    target_column: str = "label_binary",
    random_seed: int = 42,
    enable_smote: bool = False,
) -> ClassBalanceReportResult:
    """Build a TRAIN/VALIDATION/TEST class balance report."""
    train_rows = split_rows.get(TRAIN_ROLE, [])
    train_result = balance_split(
        train_rows,
        role=TRAIN_ROLE,
        method=train_method,
        target_column=target_column,
        random_seed=random_seed,
        enable_smote=enable_smote,
    )
    split_results: dict[str, ClassBalanceResult] = {TRAIN_ROLE: train_result}
    for role in (VALIDATION_ROLE, TEST_ROLE):
        split_results[role] = balance_split(
            split_rows.get(role, []),
            role=role,
            method=BALANCING_NONE,
            target_column=target_column,
            random_seed=random_seed,
            enable_smote=False,
        )
    validation_test_not_modified = all(
        split_results[role].validation_test_not_modified for role in (VALIDATION_ROLE, TEST_ROLE)
    )
    warnings = [
        warning
        for result in split_results.values()
        for warning in result.warnings
    ]
    return ClassBalanceReportResult(
        status="SUCCESS",
        balancing_method=train_result.method,
        splits=split_results,
        class_weight_metadata=compute_class_weight_metadata(train_result.before_distribution),
        validation_test_not_modified=validation_test_not_modified,
        smote_enabled=train_result.smote_enabled,
        warnings=_unique(warnings),
    )


def _random_undersample(
    rows: list[dict[str, Any]],
    *,
    target_column: str,
    random_seed: int,
) -> tuple[list[dict[str, Any]], bool, list[str]]:
    grouped, unlabeled = _group_labeled_rows(rows, target_column=target_column)
    warnings = _resampling_warnings(grouped)
    if warnings:
        return rows, False, warnings
    target_size = min(len(items) for items in grouped.values())
    rng = random.Random(random_seed)
    selected: list[dict[str, Any]] = []
    for label in sorted(grouped):
        selected.extend(rng.sample(grouped[label], target_size))
    return [*selected, *unlabeled], True, []


def _random_oversample(
    rows: list[dict[str, Any]],
    *,
    target_column: str,
    random_seed: int,
) -> tuple[list[dict[str, Any]], bool, list[str]]:
    grouped, unlabeled = _group_labeled_rows(rows, target_column=target_column)
    warnings = _resampling_warnings(grouped)
    if warnings:
        return rows, False, warnings
    target_size = max(len(items) for items in grouped.values())
    rng = random.Random(random_seed)
    output: list[dict[str, Any]] = []
    for label in sorted(grouped):
        items = [dict(row) for row in grouped[label]]
        while len(items) < target_size:
            items.append(dict(rng.choice(grouped[label])))
        output.extend(items)
    return [*output, *[dict(row) for row in unlabeled]], True, []


def _group_labeled_rows(
    rows: list[dict[str, Any]],
    *,
    target_column: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unlabeled: list[dict[str, Any]] = []
    for row in rows:
        label = _normalize_label(row.get(target_column))
        if label is None:
            unlabeled.append(dict(row))
        else:
            grouped[label].append(dict(row))
    return dict(grouped), unlabeled


def _resampling_warnings(grouped: dict[str, list[dict[str, Any]]]) -> list[str]:
    if len(grouped) < 2:
        return ["physical resampling skipped because fewer than two labeled classes are present"]
    if any(not rows for rows in grouped.values()):
        return ["physical resampling skipped because at least one class is empty"]
    return []


def _distribution_warnings(distribution: ClassDistribution) -> list[str]:
    warnings: list[str] = []
    if distribution.missing_label_count:
        warnings.append(
            f"{distribution.role} has {distribution.missing_label_count} missing/unlabeled labels; they are not treated as benign"
        )
    if distribution.labeled_count == 0:
        warnings.append(f"{distribution.role} has no labeled rows for class balance metadata")
    return warnings


def _normalize_role(role: str) -> str:
    normalized = role.strip().upper()
    if normalized not in SPLIT_ROLES:
        allowed = ", ".join(SPLIT_ROLES)
        raise ValueError(f"unsupported split role={role!r}; allowed values: {allowed}")
    return normalized


def _normalize_method(method: str) -> str:
    normalized = method.strip().lower()
    if normalized not in BALANCING_METHODS:
        allowed = ", ".join(BALANCING_METHODS)
        raise ValueError(f"unsupported balancing method={method!r}; allowed values: {allowed}")
    return normalized


def _normalize_label(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, (int, float)) and value in {0, 1}:
        return str(int(value))
    text = str(value).strip().lower()
    if text in {"1", "true", "attack", "malicious", "exfiltration"}:
        return "1"
    if text in {"0", "false", "benign", "normal"}:
        return "0"
    return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _unique(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values
