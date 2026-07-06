"""TRAIN-fitted categorical encoding for Stage Three preprocessing."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

import pyarrow as pa

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.missing_values import TRAIN_ROLE, PreprocessingFitRoleError


UNKNOWN_CATEGORY = "UNKNOWN"
FORBIDDEN_ENCODING_COLUMNS = frozenset(
    {
        "dataset_name",
        "dataset_role",
        "source_file",
        "source_path",
        "source_file_path",
        "scenario_name",
        "label_source",
        "label_status",
        "parser_name",
        "parser_version",
    }
)
SMALL_CARDINALITY_LIMIT = 16
DEFAULT_HASH_BUCKETS = 32


@dataclass(frozen=True)
class EncoderColumnState:
    """Fitted encoding strategy and categories for one categorical feature."""

    column: str
    catalog_dtype: str
    requested_strategy: str
    strategy: str
    categories: list[str] = field(default_factory=list)
    frequencies: dict[str, float] = field(default_factory=dict)
    token_to_index: dict[str, int] = field(default_factory=dict)
    hash_buckets: int = DEFAULT_HASH_BUCKETS
    unknown_value: str = UNKNOWN_CATEGORY


@dataclass(frozen=True)
class CategoricalEncoderArtifact:
    """TRAIN-fitted categorical encoder metadata."""

    fit_role: str
    columns: dict[str, EncoderColumnState]
    rejected_columns: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly encoder metadata."""
        return {
            "fit_role": self.fit_role,
            "columns": {name: asdict(state) for name, state in self.columns.items()},
            "rejected_columns": dict(self.rejected_columns),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CategoricalEncodingResult:
    """Rows after categorical encoding plus unknown-category metrics."""

    rows: list[dict[str, Any]]
    artifact: CategoricalEncoderArtifact
    encoded_columns: list[str]
    unknown_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return report-friendly encoding metadata."""
        return {
            "fit_role": self.artifact.fit_role,
            "encoded_columns": list(self.encoded_columns),
            "encoder_strategies": {
                name: {
                    "requested_strategy": state.requested_strategy,
                    "strategy": state.strategy,
                    "category_count": len(state.categories),
                    "hash_buckets": state.hash_buckets,
                }
                for name, state in self.artifact.columns.items()
            },
            "unknown_category_handling": "map unseen values to UNKNOWN/other without failing transform",
            "unknown_counts": dict(self.unknown_counts),
            "rejected_columns": dict(self.artifact.rejected_columns),
        }


def fit_categorical_encoder(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    role: str,
    feature_catalog: dict[str, Any] | None = None,
    small_cardinality_limit: int = SMALL_CARDINALITY_LIMIT,
    hash_buckets: int = DEFAULT_HASH_BUCKETS,
) -> CategoricalEncoderArtifact:
    """Fit categorical encoder metadata on TRAIN rows only."""
    _require_train_role(role)
    input_rows = _rows(rows)
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    specs = _catalog_categorical_specs(catalog)
    states: dict[str, EncoderColumnState] = {}
    rejected: dict[str, str] = {}
    for column, spec in specs.items():
        if column in FORBIDDEN_ENCODING_COLUMNS:
            rejected[column] = "forbidden source/leakage column excluded from encoding"
            continue
        if not any(column in row for row in input_rows):
            continue
        requested = str(spec.get("encoding", "none")).strip() or "none"
        values = [_normalize_category(row.get(column)) for row in input_rows]
        categories = sorted({UNKNOWN_CATEGORY, *values})
        counts = Counter(values)
        strategy = _resolved_strategy(requested, categories, small_cardinality_limit)
        total = len(values) or 1
        states[column] = EncoderColumnState(
            column=column,
            catalog_dtype=str(spec.get("dtype", "")),
            requested_strategy=requested,
            strategy=strategy,
            categories=categories if strategy in {"one_hot", "ordinal"} else [],
            frequencies={category: counts[category] / total for category in sorted(counts)},
            token_to_index=_token_to_index(categories) if strategy == "token_id" else {},
            hash_buckets=hash_buckets,
        )
    return CategoricalEncoderArtifact(
        fit_role=TRAIN_ROLE,
        columns=states,
        rejected_columns=rejected,
        metadata={
            "stage": "stage-three",
            "task": "Task13-missing-values-and-categorical-encoding",
            "artifact_type": "categorical_encoder",
        },
    )


def transform_categorical_features(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    artifact: CategoricalEncoderArtifact,
) -> CategoricalEncodingResult:
    """Transform rows with a TRAIN-fitted categorical encoder artifact."""
    input_rows = [dict(row) for row in _rows(rows)]
    output_rows: list[dict[str, Any]] = []
    encoded_columns: list[str] = []
    unknown_counts: dict[str, int] = {column: 0 for column in artifact.columns}
    for row in input_rows:
        encoded_row = dict(row)
        for column, state in artifact.columns.items():
            raw_value = encoded_row.pop(column, None)
            category = _normalize_category(raw_value)
            known = _is_known_category(category, state)
            if not known:
                unknown_counts[column] += 1
                category = state.unknown_value
            _encode_value(encoded_row, column=column, category=category, state=state)
        output_rows.append(encoded_row)
    for row in output_rows:
        for column in row:
            if "__onehot_" in column or column.endswith("__freq") or column.endswith("__hash_bucket") or column.endswith("__token_id") or column.endswith("__ordinal"):
                if column not in encoded_columns:
                    encoded_columns.append(column)
    return CategoricalEncodingResult(
        rows=output_rows,
        artifact=artifact,
        encoded_columns=encoded_columns,
        unknown_counts=unknown_counts,
    )


def _encode_value(
    row: dict[str, Any],
    *,
    column: str,
    category: str,
    state: EncoderColumnState,
) -> None:
    if state.strategy == "one_hot":
        for fitted_category in state.categories:
            safe_category = _safe_name(fitted_category)
            row[f"{column}__onehot_{safe_category}"] = 1 if category == fitted_category else 0
        return
    if state.strategy == "frequency":
        row[f"{column}__freq"] = float(state.frequencies.get(category, state.frequencies.get(UNKNOWN_CATEGORY, 0.0)))
        return
    if state.strategy == "hashing":
        row[f"{column}__hash_bucket"] = _hash_bucket(category, state.hash_buckets)
        return
    if state.strategy == "token_id":
        row[f"{column}__token_id"] = state.token_to_index.get(category, state.token_to_index[UNKNOWN_CATEGORY])
        return
    if state.strategy == "ordinal":
        category_to_index = {value: index for index, value in enumerate(state.categories)}
        row[f"{column}__ordinal"] = category_to_index.get(category, category_to_index[UNKNOWN_CATEGORY])
        return
    row[column] = category


def _catalog_categorical_specs(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
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
            dtype = str(feature.get("dtype", "")).strip()
            if dtype not in {"categorical", "text_token", "token_sequence"}:
                continue
            name = feature.get("name")
            preprocessing = feature.get("preprocessing", {})
            if isinstance(name, str) and name.strip() and isinstance(preprocessing, dict):
                specs[name.strip()] = {
                    "dtype": dtype,
                    "encoding": str(preprocessing.get("encoding", "none")).strip() or "none",
                }
    return specs


def _resolved_strategy(requested: str, categories: list[str], small_cardinality_limit: int) -> str:
    if requested == "one_hot":
        return "one_hot" if len(categories) <= small_cardinality_limit else "frequency"
    if requested == "hashing":
        return "hashing"
    if requested == "token_id":
        return "token_id"
    if requested == "ordinal":
        return "ordinal"
    return "frequency"


def _token_to_index(categories: list[str]) -> dict[str, int]:
    ordered = [UNKNOWN_CATEGORY, *[category for category in categories if category != UNKNOWN_CATEGORY]]
    return {category: index for index, category in enumerate(ordered)}


def _is_known_category(category: str, state: EncoderColumnState) -> bool:
    if state.strategy in {"one_hot", "ordinal"}:
        return category in state.categories
    if state.strategy == "token_id":
        return category in state.token_to_index
    if state.strategy == "frequency":
        return category in state.frequencies
    return True


def _normalize_category(value: Any) -> str:
    if value is None:
        return UNKNOWN_CATEGORY
    text = str(value).strip()
    return text if text else UNKNOWN_CATEGORY


def _safe_name(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_") or "unknown"


def _hash_bucket(value: str, bucket_count: int) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % bucket_count


def _require_train_role(role: str) -> None:
    if role.strip().upper() != TRAIN_ROLE:
        raise PreprocessingFitRoleError("categorical encoder fit is allowed only on TRAIN")


def _rows(rows: list[dict[str, Any]] | pa.Table) -> list[dict[str, Any]]:
    if isinstance(rows, pa.Table):
        return rows.to_pylist()
    return rows
