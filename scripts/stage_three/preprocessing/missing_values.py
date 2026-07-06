"""TRAIN-fitted missing value handling for Stage Three preprocessing."""

from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass, field
from typing import Any

import pyarrow as pa

from scripts.stage_three.feature_catalog.loader import load_feature_catalog


TRAIN_ROLE = "TRAIN"


class PreprocessingFitRoleError(ValueError):
    """Raised when fitting preprocessing on a non-TRAIN split."""


@dataclass(frozen=True)
class ImputerColumnState:
    """Fitted missing-value strategy and statistics for one feature."""

    column: str
    catalog_dtype: str
    strategy: str
    fill_value: Any
    missing_ratio_fit: float
    add_indicator: bool


@dataclass(frozen=True)
class MissingValueImputerArtifact:
    """TRAIN-fitted imputer metadata used for transform-only split processing."""

    fit_role: str
    columns: dict[str, ImputerColumnState]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly imputer metadata."""
        return {
            "fit_role": self.fit_role,
            "columns": {name: asdict(state) for name, state in self.columns.items()},
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class MissingValueTransformResult:
    """Rows after imputation plus before/after missing-ratio metadata."""

    rows: list[dict[str, Any]]
    artifact: MissingValueImputerArtifact
    missing_ratios_before: dict[str, float]
    missing_ratios_after: dict[str, float]
    added_indicators: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return report-friendly transform metadata."""
        return {
            "fit_role": self.artifact.fit_role,
            "missing_ratios_before": self.missing_ratios_before,
            "missing_ratios_after": self.missing_ratios_after,
            "added_indicators": list(self.added_indicators),
            "imputer_strategies": {
                name: {
                    "catalog_dtype": state.catalog_dtype,
                    "strategy": state.strategy,
                    "fill_value": state.fill_value,
                    "add_indicator": state.add_indicator,
                }
                for name, state in self.artifact.columns.items()
            },
        }


def fit_missing_value_imputer(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    role: str,
    feature_catalog: dict[str, Any] | None = None,
    add_missing_indicators: bool = True,
) -> MissingValueImputerArtifact:
    """Fit missing-value statistics on TRAIN rows only."""
    _require_train_role(role)
    input_rows = _rows(rows)
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    specs = _catalog_feature_specs(catalog)
    states: dict[str, ImputerColumnState] = {}
    for column, spec in specs.items():
        if not _column_present(input_rows, column):
            continue
        values = [row.get(column) for row in input_rows]
        strategy = str(spec.get("missing", "none")).strip() or "none"
        dtype = str(spec.get("dtype", ""))
        missing_ratio = _missing_ratio(values)
        states[column] = ImputerColumnState(
            column=column,
            catalog_dtype=dtype,
            strategy=strategy,
            fill_value=_fit_fill_value(values, strategy=strategy, dtype=dtype),
            missing_ratio_fit=missing_ratio,
            add_indicator=add_missing_indicators and strategy != "none",
        )
    return MissingValueImputerArtifact(
        fit_role=TRAIN_ROLE,
        columns=states,
        metadata={
            "stage": "stage-three",
            "task": "Task13-missing-values-and-categorical-encoding",
            "artifact_type": "missing_value_imputer",
        },
    )


def transform_missing_values(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    artifact: MissingValueImputerArtifact,
) -> MissingValueTransformResult:
    """Transform rows using a TRAIN-fitted imputer artifact."""
    input_rows = _rows(rows)
    output_rows = [dict(row) for row in input_rows]
    before: dict[str, float] = {}
    after: dict[str, float] = {}
    added_indicators: list[str] = []
    for column, state in artifact.columns.items():
        values_before = [row.get(column) for row in output_rows]
        before[column] = _missing_ratio(values_before)
        indicator_name = f"{column}__missing"
        if state.add_indicator:
            added_indicators.append(indicator_name)
        for row in output_rows:
            missing = _is_missing(row.get(column))
            if state.add_indicator:
                row[indicator_name] = 1 if missing else 0
            if missing:
                row[column] = _copy_fill_value(state.fill_value)
        after[column] = _missing_ratio([row.get(column) for row in output_rows])
    return MissingValueTransformResult(
        rows=output_rows,
        artifact=artifact,
        missing_ratios_before=before,
        missing_ratios_after=after,
        added_indicators=added_indicators,
    )


def _fit_fill_value(values: list[Any], *, strategy: str, dtype: str) -> Any:
    if strategy == "none":
        return None
    if strategy in {"zero", "false"}:
        return [0.0] * _vector_length(values) if dtype == "numeric_vector" else 0
    if strategy in {"unknown", "constant"}:
        return "UNKNOWN"
    if strategy == "empty":
        return []
    numeric_values = [_to_float(value) for value in values if not _is_missing(value)]
    numeric_values = [value for value in numeric_values if value is not None]
    if strategy == "median":
        return float(statistics.median(numeric_values)) if numeric_values else 0.0
    if strategy == "mean":
        return float(statistics.fmean(numeric_values)) if numeric_values else 0.0
    if strategy == "most_frequent":
        present = [value for value in values if not _is_missing(value)]
        if not present:
            return "UNKNOWN" if dtype in {"categorical", "text_token", "token_sequence"} else 0
        return max(sorted(set(present), key=str), key=present.count)
    if strategy == "drop":
        return None
    return 0


def _catalog_feature_specs(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    groups = catalog.get("feature_groups", {})
    if not isinstance(groups, dict):
        return specs
    for group in groups.values():
        if not isinstance(group, dict):
            continue
        features = group.get("features", [])
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict) or feature.get("allow_in_X") is not True:
                continue
            name = feature.get("name")
            preprocessing = feature.get("preprocessing", {})
            if isinstance(name, str) and name.strip() and isinstance(preprocessing, dict):
                specs[name.strip()] = {
                    "dtype": str(feature.get("dtype", "")).strip(),
                    "missing": str(preprocessing.get("missing", "none")).strip() or "none",
                }
    return specs


def _require_train_role(role: str) -> None:
    if role.strip().upper() != TRAIN_ROLE:
        raise PreprocessingFitRoleError("missing-value imputer fit is allowed only on TRAIN")


def _rows(rows: list[dict[str, Any]] | pa.Table) -> list[dict[str, Any]]:
    if isinstance(rows, pa.Table):
        return rows.to_pylist()
    return rows


def _column_present(rows: list[dict[str, Any]], column: str) -> bool:
    return any(column in row for row in rows)


def _missing_ratio(values: list[Any]) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if _is_missing(value)) / len(values)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, float):
        return math.isnan(value)
    return False


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _vector_length(values: list[Any]) -> int:
    for value in values:
        if isinstance(value, (list, tuple)):
            return len(value)
    return 0


def _copy_fill_value(value: Any) -> Any:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value
