"""TRAIN-fitted scaling profiles for Stage Three preprocessing."""

from __future__ import annotations

import json
import math
import struct
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from config import STAGE_THREE_BATCH_ROWS, STAGE_TWO_PARQUET_COMPRESSION
from scripts.db.models import PreprocessingArtifact as CatalogPreprocessingArtifact
from scripts.db.repositories import PreprocessingRepository
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.missing_values import (
    TRAIN_ROLE,
    PreprocessingFitRoleError,
)
from scripts.stage_three.preprocessing.profiles import (
    DL_ALLOWED_SCALERS,
    DL_SCALED_PROFILE,
    SCALING_PROFILES,
    TREE_UNSCALED_PROFILE,
    ScalingProfile,
    get_scaling_profile,
    resolve_scaler_for_feature,
)
from scripts.stage_two.model_ready.contracts import (
    MODEL_READY_SCHEMA_VERSION,
    validate_preprocessing_fit_role,
)


SCALING_ARTIFACT_SCHEMA_NAME = "preprocessing_scaler"
SCALING_ARTIFACT_SCHEMA_VERSION = "v1"
NUMERIC_DTYPES = frozenset({"integer", "numeric", "duration", "boolean"})
VECTOR_DTYPES = frozenset({"numeric_vector"})


class SparseScalingError(ValueError):
    """Raised when a scaling operation would densify a sparse input."""


@dataclass(frozen=True)
class ScalerColumnState:
    """Fitted scaling statistics for one feature column."""

    column: str
    catalog_dtype: str
    strategy: str
    center: float = 0.0
    scale: float = 1.0
    mean: float | None = None
    std: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    fitted_count: int = 0
    output_dtype: str = "float32"
    sparse_safe: bool = True


@dataclass(frozen=True)
class ScalingArtifact:
    """TRAIN-fitted scaler metadata for one scaling profile."""

    fit_role: str
    profile_name: str
    profile: ScalingProfile
    columns: dict[str, ScalerColumnState]
    feature_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly scaler metadata."""
        return {
            "fit_role": self.fit_role,
            "profile_name": self.profile_name,
            "profile": self.profile.to_dict(),
            "columns": {name: asdict(state) for name, state in self.columns.items()},
            "feature_count": self.feature_count,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ScalingTransformResult:
    """Rows after scaling plus audit metadata."""

    rows: list[dict[str, Any]]
    artifact: ScalingArtifact
    split_role: str
    scaled_columns: list[str]
    feature_count: int
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return report-friendly scaling transform metadata."""
        return {
            "split_role": self.split_role,
            "fit_role": self.artifact.fit_role,
            "profile_name": self.artifact.profile_name,
            "row_count": len(self.rows),
            "feature_count": self.feature_count,
            "scaled_columns": list(self.scaled_columns),
            "scaler_statistics_location": self.artifact.metadata.get(
                "statistics_path",
                self.artifact.metadata.get("artifact_path", ""),
            ),
            "scaler": self.artifact.to_dict(),
            "report_paths": dict(self.report_paths),
        }


@dataclass(frozen=True)
class PreprocessingArtifactRegistrationSummary:
    """Catalog registration result for a preprocessing artifact."""

    preprocessing_artifact_ids: list[int]
    artifact_path: str
    fitted_on_role: str
    profile_name: str
    feature_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return report-friendly registration metadata."""
        return asdict(self)


def available_scaling_profiles() -> dict[str, dict[str, Any]]:
    """Return all supported scaling profiles."""
    return {name: profile.to_dict() for name, profile in SCALING_PROFILES.items()}


def fit_scaling_artifact(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    role: str,
    profile_name: str,
    feature_catalog: dict[str, Any] | None = None,
) -> ScalingArtifact:
    """Fit scaler statistics on TRAIN rows only."""
    _require_train_role(role)
    input_rows = _rows(rows)
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    specs = _catalog_scaling_specs(catalog)
    return _fit_from_row_iterable(
        input_rows,
        profile_name=profile_name,
        specs=specs,
        metadata={
            "stage": "stage-three",
            "task": "Task14-scaling-profiles-and-preprocessing-artifacts",
            "artifact_type": "scaler",
            "fit_source": "rows",
        },
    )


def fit_scaling_artifact_from_parquet(
    paths: Iterable[str | Path],
    *,
    role: str,
    profile_name: str,
    feature_catalog: dict[str, Any] | None = None,
    batch_rows: int = STAGE_THREE_BATCH_ROWS,
) -> ScalingArtifact:
    """Fit scaler statistics from TRAIN Parquet batches without loading all splits."""
    _require_train_role(role)
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    specs = _catalog_scaling_specs(catalog)
    row_batches = (
        row
        for path in paths
        for batch in pq.ParquetFile(path).iter_batches(batch_size=batch_rows)
        for row in pa.Table.from_batches([batch]).to_pylist()
    )
    return _fit_from_row_iterable(
        row_batches,
        profile_name=profile_name,
        specs=specs,
        metadata={
            "stage": "stage-three",
            "task": "Task14-scaling-profiles-and-preprocessing-artifacts",
            "artifact_type": "scaler",
            "fit_source": "parquet_batches",
            "batch_rows": batch_rows,
        },
    )


def transform_scaling(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    artifact: ScalingArtifact,
    role: str,
) -> ScalingTransformResult:
    """Transform one split with TRAIN-fitted scaler statistics."""
    input_rows = _rows(rows)
    output_rows = [_scale_row(row, artifact=artifact) for row in input_rows]
    return ScalingTransformResult(
        rows=output_rows,
        artifact=artifact,
        split_role=role.strip().upper(),
        scaled_columns=list(artifact.columns),
        feature_count=_feature_count(output_rows),
    )


def transform_scaling_table(
    table: pa.Table,
    *,
    artifact: ScalingArtifact,
    role: str,
) -> tuple[pa.Table, ScalingTransformResult]:
    """Transform a PyArrow table and cast scaled columns to float32."""
    result = transform_scaling(table, artifact=artifact, role=role)
    return _rows_to_table(result.rows, scaled_columns=set(result.scaled_columns)), result


def transform_parquet_file_in_chunks(
    input_path: str | Path,
    output_path: str | Path,
    *,
    artifact: ScalingArtifact,
    role: str,
    batch_rows: int = STAGE_THREE_BATCH_ROWS,
    compression: str | None = None,
) -> ScalingTransformResult:
    """Transform one Parquet artifact in record batches and write a scaled Parquet file."""
    source = Path(input_path).expanduser()
    target = Path(output_path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    parquet_file = pq.ParquetFile(source)
    writer: pq.ParquetWriter | None = None
    total_rows = 0
    scaled_columns = set(artifact.columns)
    try:
        for batch in parquet_file.iter_batches(batch_size=batch_rows):
            table, batch_result = transform_scaling_table(
                pa.Table.from_batches([batch]),
                artifact=artifact,
                role=role,
            )
            if writer is None:
                writer = pq.ParquetWriter(
                    target,
                    table.schema,
                    compression=(compression or STAGE_TWO_PARQUET_COMPRESSION or "zstd"),
                )
            writer.write_table(table)
            total_rows += len(batch_result.rows)
    finally:
        if writer is not None:
            writer.close()
    return ScalingTransformResult(
        rows=[],
        artifact=artifact,
        split_role=role.strip().upper(),
        scaled_columns=list(scaled_columns),
        feature_count=len(scaled_columns),
        report_paths={},
    )


def write_scaling_artifact_json(
    artifact: ScalingArtifact,
    path: str | Path,
) -> ScalingArtifact:
    """Write scaler statistics to JSON and return an artifact with the path recorded."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = artifact.to_dict()
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    metadata = dict(artifact.metadata)
    metadata["statistics_path"] = target.as_posix()
    metadata["artifact_path"] = target.as_posix()
    return replace(artifact, metadata=metadata)


def register_scaling_preprocessing_artifact(
    repository: PreprocessingRepository,
    artifact: ScalingArtifact,
    *,
    branch: str,
    artifact_path: str | Path,
    feature_group: str | None = None,
    fitted_on_feature_artifact_id: int | None = None,
    status: str = "SUCCESS",
) -> tuple[CatalogPreprocessingArtifact, PreprocessingArtifactRegistrationSummary]:
    """Register a TRAIN-fitted scaler as a preprocessing_artifacts catalog row."""
    validate_preprocessing_fit_role(artifact.fit_role)
    catalog_artifact = repository.register_preprocessing_artifact(
        artifact_uid=uuid4(),
        branch=branch,
        feature_group=feature_group,
        preprocessing_type=f"scaler:{artifact.profile_name}",
        artifact_path=Path(artifact_path).as_posix(),
        fitted_on_role=artifact.fit_role,
        fitted_on_feature_artifact_id=fitted_on_feature_artifact_id,
        schema_version=MODEL_READY_SCHEMA_VERSION,
        object_version=SCALING_ARTIFACT_SCHEMA_VERSION,
        columns_json={
            "scaled_columns": list(artifact.columns),
            "feature_count": artifact.feature_count,
        },
        params_json=artifact.to_dict(),
        status=status,
    )
    return catalog_artifact, PreprocessingArtifactRegistrationSummary(
        preprocessing_artifact_ids=[int(catalog_artifact.id)],
        artifact_path=Path(artifact_path).as_posix(),
        fitted_on_role=artifact.fit_role,
        profile_name=artifact.profile_name,
        feature_count=artifact.feature_count,
    )


def transform_sparse_matrix(
    matrix: Any,
    *,
    artifact: ScalingArtifact,
    columns: list[str],
) -> Any:
    """Scale sparse matrices without centering or densifying."""
    if not _looks_sparse(matrix):
        raise TypeError("matrix does not look like a sparse matrix")
    multipliers: list[float] = []
    for column in columns:
        state = artifact.columns.get(column)
        if state is None:
            multipliers.append(1.0)
            continue
        if not _is_zeroish(state.center):
            raise SparseScalingError(
                f"sparse-safe scaling cannot center column {column!r}; use tree_unscaled or a no-centering sparse path"
            )
        multipliers.append(1.0 / state.scale if state.scale else 1.0)
    return matrix.multiply(multipliers)


def _fit_from_row_iterable(
    rows: Iterable[dict[str, Any]],
    *,
    profile_name: str,
    specs: dict[str, dict[str, Any]],
    metadata: dict[str, Any],
) -> ScalingArtifact:
    profile = get_scaling_profile(profile_name)
    values_by_column: dict[str, list[float]] = {}
    for row in rows:
        for column, spec in specs.items():
            if column not in row:
                continue
            strategy = resolve_scaler_for_feature(
                profile.name,
                feature_policy=str(spec.get("scaling", "none")),
                is_numeric=bool(spec.get("is_numeric", False)),
            )
            if strategy == "none":
                continue
            value = _to_float(row.get(column))
            if value is None:
                continue
            values_by_column.setdefault(column, []).append(value)

    states: dict[str, ScalerColumnState] = {}
    for column, values in values_by_column.items():
        spec = specs[column]
        strategy = resolve_scaler_for_feature(
            profile.name,
            feature_policy=str(spec.get("scaling", "none")),
            is_numeric=bool(spec.get("is_numeric", False)),
        )
        if strategy == "none":
            continue
        states[column] = _fit_column_state(
            column=column,
            dtype=str(spec.get("dtype", "")),
            strategy=strategy,
            values=values,
        )
    if profile.name == DL_SCALED_PROFILE:
        _validate_dl_scalers(states)
    return ScalingArtifact(
        fit_role=TRAIN_ROLE,
        profile_name=profile.name,
        profile=profile,
        columns=states,
        feature_count=len(states),
        metadata=metadata,
    )


def _fit_column_state(
    *,
    column: str,
    dtype: str,
    strategy: str,
    values: list[float],
) -> ScalerColumnState:
    count = len(values)
    if strategy == "standard":
        mean = sum(values) / count if count else 0.0
        variance = sum((value - mean) ** 2 for value in values) / count if count else 0.0
        std = math.sqrt(variance)
        scale = std if std > 0.0 else 1.0
        return ScalerColumnState(
            column=column,
            catalog_dtype=dtype,
            strategy=strategy,
            center=mean,
            scale=scale,
            mean=mean,
            std=std,
            fitted_count=count,
        )
    if strategy == "robust":
        median = _quantile(values, 0.5)
        q1 = _quantile(values, 0.25)
        q3 = _quantile(values, 0.75)
        iqr = q3 - q1
        scale = iqr if iqr > 0.0 else 1.0
        return ScalerColumnState(
            column=column,
            catalog_dtype=dtype,
            strategy=strategy,
            center=median,
            scale=scale,
            median=median,
            q1=q1,
            q3=q3,
            fitted_count=count,
        )
    if strategy == "minmax":
        min_value = min(values) if values else 0.0
        max_value = max(values) if values else 0.0
        range_value = max_value - min_value
        scale = range_value if range_value > 0.0 else 1.0
        return ScalerColumnState(
            column=column,
            catalog_dtype=dtype,
            strategy=strategy,
            center=min_value,
            scale=scale,
            min_value=min_value,
            max_value=max_value,
            fitted_count=count,
        )
    raise ValueError(f"unsupported scaler strategy={strategy!r}")


def _scale_row(row: dict[str, Any], *, artifact: ScalingArtifact) -> dict[str, Any]:
    output = dict(row)
    for column, state in artifact.columns.items():
        value = output.get(column)
        if _looks_sparse(value):
            output[column] = transform_sparse_matrix(value, artifact=artifact, columns=[column])
            continue
        number = _to_float(value)
        if number is None:
            output[column] = None
            continue
        output[column] = _float32((number - state.center) / state.scale)
    return output


def _catalog_scaling_specs(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
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
            dtype = str(feature.get("dtype", "")).strip()
            if not isinstance(name, str) or not name.strip() or not isinstance(preprocessing, dict):
                continue
            specs[name.strip()] = {
                "dtype": dtype,
                "scaling": str(preprocessing.get("scaling", "none")).strip().lower() or "none",
                "is_numeric": dtype in NUMERIC_DTYPES or dtype in VECTOR_DTYPES,
            }
    return specs


def _require_train_role(role: str) -> None:
    if role.strip().upper() != TRAIN_ROLE:
        raise PreprocessingFitRoleError("scaler fit is allowed only on TRAIN")


def _validate_dl_scalers(states: dict[str, ScalerColumnState]) -> None:
    invalid = sorted(
        {state.strategy for state in states.values() if state.strategy not in DL_ALLOWED_SCALERS}
    )
    if invalid:
        raise ValueError(f"dl_scaled supports only standard/minmax scalers, got: {', '.join(invalid)}")


def _rows(rows: list[dict[str, Any]] | pa.Table) -> list[dict[str, Any]]:
    if isinstance(rows, pa.Table):
        return rows.to_pylist()
    return rows


def _rows_to_table(rows: list[dict[str, Any]], *, scaled_columns: set[str]) -> pa.Table:
    columns = _ordered_columns(rows)
    arrays: dict[str, pa.Array] = {}
    for column in columns:
        values = [row.get(column) for row in rows]
        if column in scaled_columns:
            arrays[column] = pa.array(values, type=pa.float32())
        else:
            arrays[column] = pa.array(values)
    return pa.table(arrays)


def _ordered_columns(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _feature_count(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    return len(set().union(*(row.keys() for row in rows)))


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _float32(value: float) -> float:
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _looks_sparse(value: Any) -> bool:
    return all(hasattr(value, attr) for attr in ("multiply", "shape")) and (
        hasattr(value, "tocsr") or hasattr(value, "tocsc")
    )


def _is_zeroish(value: float) -> bool:
    return abs(value) <= 1e-12
