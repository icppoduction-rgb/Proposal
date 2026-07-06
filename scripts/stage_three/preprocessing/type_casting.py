"""Feature type casting and stable schema normalization for Stage Three X tables."""

from __future__ import annotations

import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from config import STAGE_THREE_BATCH_ROWS
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS


ENCODING_DTYPES = frozenset({"categorical", "text_token", "token_sequence"})
FLOAT32_DTYPES = frozenset({"numeric", "duration"})
INTEGER_DTYPES = frozenset({"integer"})
BOOLEAN_DTYPES = frozenset({"boolean", "binary"})
VECTOR_DTYPES = frozenset({"numeric_vector"})
RAW_TIMESTAMP_COLUMNS = frozenset({"timestamp", "event_timestamp", "created_at", "updated_at"})
RAW_OBJECT_HINTS = frozenset({"json", "payload", "body", "raw", "path", "source", "scenario"})
INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1


@dataclass(frozen=True)
class DTypeConversion:
    """One column dtype conversion applied to model-ready X."""

    column: str
    catalog_dtype: str
    output_dtype: str
    nullable: bool
    action: str
    memory_before_bytes: int
    memory_after_bytes: int


@dataclass(frozen=True)
class RejectedColumn:
    """One column excluded from typed X before downstream preprocessing."""

    column: str
    reason: str
    catalog_dtype: str | None = None


@dataclass(frozen=True)
class SchemaWarning:
    """Non-blocking schema warning emitted during type casting."""

    column: str
    message: str


@dataclass(frozen=True)
class TypeCastingResult:
    """Typed X table plus schema metadata for downstream preprocessing."""

    status: str
    typed_X: pa.Table
    dtype_conversions: list[DTypeConversion]
    rejected_columns: list[RejectedColumn] = field(default_factory=list)
    schema_warnings: list[SchemaWarning] = field(default_factory=list)
    memory_before_bytes: int = 0
    memory_after_bytes: int = 0
    schema_metadata: dict[str, Any] = field(default_factory=dict)
    report_paths: dict[str, str] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        """Return typed X row count."""
        return self.typed_X.num_rows

    @property
    def typed_columns(self) -> list[str]:
        """Return typed X column names."""
        return list(self.typed_X.schema.names)

    def to_dict(self) -> dict[str, Any]:
        """Return a report-friendly payload without embedding table data."""
        return {
            "status": self.status,
            "row_count": self.row_count,
            "typed_columns": self.typed_columns,
            "dtype_conversions": [asdict(item) for item in self.dtype_conversions],
            "rejected_columns": [asdict(item) for item in self.rejected_columns],
            "schema_warnings": [asdict(item) for item in self.schema_warnings],
            "memory_before_bytes": self.memory_before_bytes,
            "memory_after_bytes": self.memory_after_bytes,
            "schema_metadata": self.schema_metadata,
            "report_paths": dict(self.report_paths),
        }


def cast_x_table_to_typed_table(
    table: pa.Table,
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> TypeCastingResult:
    """Cast a PyArrow X table to stable ML-compatible dtypes."""
    return cast_x_rows_to_typed_table(table.to_pylist(), feature_catalog=feature_catalog)


def cast_x_batches_to_typed_table(
    row_batches: Iterable[list[dict[str, Any]]],
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> TypeCastingResult:
    """Cast row batches independently and concatenate normalized Arrow tables."""
    batch_results: list[TypeCastingResult] = []
    for batch in row_batches:
        if batch:
            batch_results.append(cast_x_rows_to_typed_table(batch, feature_catalog=feature_catalog))
    if not batch_results:
        return cast_x_rows_to_typed_table([], feature_catalog=feature_catalog)
    return _merge_batch_results(batch_results)


def cast_x_artifacts_to_typed_table(
    paths: Iterable[str | Path],
    *,
    feature_catalog: dict[str, Any] | None = None,
    batch_rows: int = STAGE_THREE_BATCH_ROWS,
) -> TypeCastingResult:
    """Read Parquet X artifacts in row batches and return one normalized typed table."""
    artifact_paths = [Path(path) for path in paths]
    if not artifact_paths:
        raise ValueError("at least one X artifact path is required")
    return cast_x_batches_to_typed_table(
        _iter_parquet_row_batches(artifact_paths, batch_rows=batch_rows),
        feature_catalog=feature_catalog,
    )


def cast_x_rows_to_typed_table(
    rows: list[dict[str, Any]],
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> TypeCastingResult:
    """Cast X rows to a stable Arrow table using feature catalog dtype metadata."""
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    feature_specs = _catalog_feature_specs(catalog)
    source_columns = _ordered_source_columns(rows)
    memory_before = _estimate_rows_memory(rows)
    arrays: list[pa.Array] = []
    fields: list[pa.Field] = []
    conversions: list[DTypeConversion] = []
    rejected: list[RejectedColumn] = []
    warnings: list[SchemaWarning] = []

    for column in source_columns:
        values = [row.get(column) for row in rows]
        spec = feature_specs.get(column)
        if _is_forbidden_or_raw_column(column, values):
            rejected.append(
                RejectedColumn(
                    column=column,
                    reason="raw/forbidden column excluded from typed X",
                    catalog_dtype=spec.get("dtype") if spec else None,
                )
            )
            continue
        if spec is None:
            rejected.append(RejectedColumn(column=column, reason="column is not declared in feature_catalog", catalog_dtype=None))
            continue

        dtype = str(spec["dtype"])
        nullable = bool(spec.get("nullable", True))
        before_bytes = _estimate_values_memory(values)
        try:
            array, output_dtype, action, extra_warnings = _cast_values(column, values, dtype=dtype)
        except (TypeError, ValueError, OverflowError) as exc:
            rejected.append(
                RejectedColumn(
                    column=column,
                    reason=f"cannot cast to {dtype}: {exc}",
                    catalog_dtype=dtype,
                )
            )
            continue
        warnings.extend(extra_warnings)
        arrays.append(array)
        fields.append(pa.field(column, array.type, nullable=True))
        conversions.append(
            DTypeConversion(
                column=column,
                catalog_dtype=dtype,
                output_dtype=output_dtype,
                nullable=nullable,
                action=action,
                memory_before_bytes=before_bytes,
                memory_after_bytes=array.nbytes,
            )
        )

    typed_table = pa.Table.from_arrays(
        arrays,
        schema=pa.schema(fields, metadata=_schema_metadata(conversions, rejected, warnings)),
    )
    result = TypeCastingResult(
        status="SUCCESS" if not rejected else "PARTIAL_SUCCESS",
        typed_X=typed_table,
        dtype_conversions=conversions,
        rejected_columns=rejected,
        schema_warnings=warnings,
        memory_before_bytes=memory_before,
        memory_after_bytes=typed_table.nbytes,
        schema_metadata=_schema_metadata_dict(conversions, rejected, warnings),
    )
    _validate_typed_table(result)
    return result


def _cast_values(
    column: str,
    values: list[Any],
    *,
    dtype: str,
) -> tuple[pa.Array, str, str, list[SchemaWarning]]:
    if dtype in FLOAT32_DTYPES:
        array = pa.array([_to_float(value) for value in values], type=pa.float32())
        return array, "float32", f"{dtype} -> float32", []
    if dtype in INTEGER_DTYPES:
        ints = [_to_int(value) for value in values]
        target_type = pa.int32() if _fits_int32(ints) else pa.int64()
        array = pa.array(ints, type=target_type)
        return array, str(target_type), f"integer -> {target_type}", []
    if dtype in BOOLEAN_DTYPES:
        array = pa.array([_to_binary_int(value) for value in values], type=pa.int8())
        return array, "int8", f"{dtype} -> int8 0/1", []
    if dtype in VECTOR_DTYPES:
        array = pa.array([_to_float_vector(value) for value in values], type=pa.list_(pa.float32()))
        return array, "list<float32>", "numeric_vector -> list<float32>", []
    if dtype in ENCODING_DTYPES:
        raise ValueError("scheduled for categorical/token encoding")
    if dtype == "datetime":
        raise ValueError("raw timestamp is not allowed in X; use derived numeric features")
    raise ValueError(f"unsupported feature catalog dtype: {dtype}")


def _validate_typed_table(result: TypeCastingResult) -> None:
    for field in result.typed_X.schema:
        if (
            pa.types.is_string(field.type)
            or pa.types.is_large_string(field.type)
            or pa.types.is_struct(field.type)
            or pa.types.is_map(field.type)
        ):
            raise TypeError(f"typed X contains non-ML-compatible dtype for {field.name}: {field.type}")
        if pa.types.is_timestamp(field.type):
            raise TypeError(f"typed X contains raw timestamp column: {field.name}")


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
            dtype = feature.get("dtype")
            if isinstance(name, str) and name.strip() and isinstance(dtype, str) and dtype.strip():
                specs[name.strip()] = {
                    "dtype": dtype.strip(),
                    "nullable": bool(feature.get("nullable", True)),
                    "preprocessing": feature.get("preprocessing", {}),
                }
    return specs


def _is_forbidden_or_raw_column(column: str, values: list[Any]) -> bool:
    if column in FORBIDDEN_X_COLUMNS or column.startswith("label_"):
        return True
    normalized = column.lower()
    if column in RAW_TIMESTAMP_COLUMNS:
        return True
    if any(hint in normalized for hint in RAW_OBJECT_HINTS):
        return True
    return any(isinstance(value, dict) for value in values if value is not None)


def _ordered_source_columns(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return float(int(value))
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        return None
    if not number.is_integer():
        raise ValueError(f"non-integer value {value!r}")
    return int(number)


def _to_binary_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in {0, 1}:
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return 1
    if text in {"0", "false", "no", "n"}:
        return 0
    raise ValueError(f"cannot convert {value!r} to binary 0/1")


def _to_float_vector(value: Any) -> list[float] | None:
    if value is None or value == "":
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"numeric_vector expects list/tuple, got {type(value).__name__}")
    converted: list[float] = []
    for item in value:
        number = _to_float(item)
        if number is None:
            converted.append(float("nan"))
        else:
            converted.append(number)
    return converted


def _fits_int32(values: list[int | None]) -> bool:
    present = [value for value in values if value is not None]
    if not present:
        return True
    return min(present) >= INT32_MIN and max(present) <= INT32_MAX


def _merge_batch_results(batch_results: list[TypeCastingResult]) -> TypeCastingResult:
    typed_table = pa.concat_tables(
        [result.typed_X for result in batch_results],
        promote_options="default",
    )
    rejected = _unique_rejected_column(
        item
        for result in batch_results
        for item in result.rejected_columns
    )
    warnings = _unique_schema_warnings(
        item
        for result in batch_results
        for item in result.schema_warnings
    )
    conversions = _merged_conversions(batch_results, typed_table)
    result = TypeCastingResult(
        status="SUCCESS" if not rejected else "PARTIAL_SUCCESS",
        typed_X=typed_table.replace_schema_metadata(
            _schema_metadata(conversions, rejected, warnings)
        ),
        dtype_conversions=conversions,
        rejected_columns=rejected,
        schema_warnings=warnings,
        memory_before_bytes=sum(result.memory_before_bytes for result in batch_results),
        memory_after_bytes=typed_table.nbytes,
        schema_metadata=_schema_metadata_dict(conversions, rejected, warnings),
    )
    _validate_typed_table(result)
    return result


def _merged_conversions(
    batch_results: list[TypeCastingResult],
    typed_table: pa.Table,
) -> list[DTypeConversion]:
    first_by_column: dict[str, DTypeConversion] = {}
    before_by_column: dict[str, int] = {}
    for result in batch_results:
        for conversion in result.dtype_conversions:
            first_by_column.setdefault(conversion.column, conversion)
            before_by_column[conversion.column] = before_by_column.get(conversion.column, 0) + conversion.memory_before_bytes
    merged: list[DTypeConversion] = []
    for field in typed_table.schema:
        original = first_by_column[field.name]
        output_dtype = str(field.type)
        merged.append(
            DTypeConversion(
                column=field.name,
                catalog_dtype=original.catalog_dtype,
                output_dtype=output_dtype,
                nullable=original.nullable,
                action=f"{original.catalog_dtype} -> {output_dtype}",
                memory_before_bytes=before_by_column[field.name],
                memory_after_bytes=typed_table.column(field.name).nbytes,
            )
        )
    return merged


def _iter_parquet_row_batches(
    artifact_paths: list[Path],
    *,
    batch_rows: int,
) -> Iterable[list[dict[str, Any]]]:
    for path in artifact_paths:
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=batch_rows):
            yield batch.to_pylist()


def _unique_rejected_column(items: Iterable[RejectedColumn]) -> list[RejectedColumn]:
    unique: dict[tuple[str, str, str | None], RejectedColumn] = {}
    for item in items:
        unique.setdefault((item.column, item.reason, item.catalog_dtype), item)
    return list(unique.values())


def _unique_schema_warnings(items: Iterable[SchemaWarning]) -> list[SchemaWarning]:
    unique: dict[tuple[str, str], SchemaWarning] = {}
    for item in items:
        unique.setdefault((item.column, item.message), item)
    return list(unique.values())


def _estimate_rows_memory(rows: list[dict[str, Any]]) -> int:
    return sum(sys.getsizeof(row) + sum(_value_size(key) + _value_size(value) for key, value in row.items()) for row in rows)


def _estimate_values_memory(values: list[Any]) -> int:
    return sum(_value_size(value) for value in values)


def _value_size(value: Any) -> int:
    if isinstance(value, dict):
        return sys.getsizeof(value) + sum(_value_size(key) + _value_size(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return sys.getsizeof(value) + sum(_value_size(item) for item in value)
    return sys.getsizeof(value)


def _schema_metadata(
    conversions: list[DTypeConversion],
    rejected: list[RejectedColumn],
    warnings: list[SchemaWarning],
) -> dict[bytes, bytes]:
    metadata = _schema_metadata_dict(conversions, rejected, warnings)
    return {str(key).encode("utf-8"): str(value).encode("utf-8") for key, value in metadata.items()}


def _schema_metadata_dict(
    conversions: list[DTypeConversion],
    rejected: list[RejectedColumn],
    warnings: list[SchemaWarning],
) -> dict[str, Any]:
    return {
        "stage": "stage-three",
        "task": "Task12-type-casting-and-schema-normalization",
        "column_count": len(conversions),
        "rejected_column_count": len(rejected),
        "schema_warning_count": len(warnings),
        "columns": {conversion.column: conversion.output_dtype for conversion in conversions},
    }
