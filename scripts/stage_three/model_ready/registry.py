"""Stage Three model-ready Parquet writer and catalog registration."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from config import PARQUET_MODEL_READY_RELATIVE, PATH_DATA_STORAGE, STAGE_TWO_PARQUET_COMPRESSION
from scripts.db.models import ModelReadyArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_three.extraction.artifact_writer import (
    AtomicParquetWriteResult,
    sha256_file,
    write_atomic_parquet_table,
)
from scripts.stage_three.model_ready.separator import validate_no_forbidden_x_columns
from scripts.stage_two.parquet.writer import ParquetWriteError
from scripts.stage_two.model_ready.contracts import (
    MODEL_READY_SCHEMA_NAME,
    MODEL_READY_SCHEMA_VERSION,
    validate_model_ready_data_type,
)


@dataclass(frozen=True)
class RegisteredModelReadyArtifact:
    """One written or resumed model-ready artifact."""

    data_type: str
    role: str
    artifact_path: str
    catalog_id: int
    sample_count: int | None
    feature_count: int | None
    resumed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a report-friendly representation."""
        return asdict(self)


class ModelReadyArtifactRegistryService:
    """Write model-ready tables atomically and register catalog records."""

    def __init__(
        self,
        *,
        storage_root: str | Path | None = None,
        compression: str | None = None,
    ) -> None:
        root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
        if not str(root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured for model-ready writes.")
        self.storage_root = root
        self.compression = (compression or STAGE_TWO_PARQUET_COMPRESSION or "zstd").strip() or "zstd"

    def artifact_path(
        self,
        *,
        experiment_id: str,
        branch: str,
        preprocessing_profile: str,
        role: str,
        file_name: str,
    ) -> Path:
        """Return the configured Stage Three model-ready artifact path."""
        return (
            self.storage_root
            / PARQUET_MODEL_READY_RELATIVE
            / _safe_segment(experiment_id)
            / _safe_segment(branch)
            / _safe_segment(preprocessing_profile)
            / _safe_segment(role.upper())
            / file_name
        )

    def register_rows(
        self,
        repository: ArtifactRepository,
        rows: list[dict[str, Any]],
        *,
        experiment_id: str,
        branch: str,
        preprocessing_profile: str,
        role: str,
        data_type: str,
        file_name: str,
        feature_artifact_id: int | None = None,
        preprocessing_artifact_id: int | None = None,
        feature_count: int | None = None,
        label_distribution_json: dict[str, Any] | None = None,
        excluded_columns_json: dict[str, Any] | None = None,
        sequence_length: int | None = None,
        metadata_json: dict[str, Any] | None = None,
        resume: bool = False,
        allow_empty: bool = False,
    ) -> RegisteredModelReadyArtifact:
        """Write rows and register them, or reuse an existing successful row in resume mode."""
        validate_model_ready_data_type(data_type)
        if data_type == "X":
            validate_no_forbidden_x_columns(rows)
        target_path = self.artifact_path(
            experiment_id=experiment_id,
            branch=branch,
            preprocessing_profile=preprocessing_profile,
            role=role,
            file_name=file_name,
        )
        relative_path = _relative_path(target_path, self.storage_root)
        if resume and target_path.exists():
            existing = repository.find_successful_model_ready_artifact(
                branch=branch,
                role=role,
                data_type=data_type,
                artifact_path=relative_path,
                schema_version=MODEL_READY_SCHEMA_VERSION,
            )
            if existing is not None:
                return RegisteredModelReadyArtifact(
                    data_type=data_type,
                    role=role,
                    artifact_path=relative_path,
                    catalog_id=int(existing.id),
                    sample_count=existing.sample_count,
                    feature_count=existing.feature_count,
                    resumed=True,
                )

        write_result = write_model_ready_rows(
            rows,
            final_path=target_path,
            storage_root=self.storage_root,
            compression=self.compression,
            allow_empty=allow_empty,
        )
        artifact = self._register_write_result(
            repository,
            write_result,
            branch=branch,
            role=role,
            data_type=data_type,
            feature_artifact_id=feature_artifact_id,
            preprocessing_artifact_id=preprocessing_artifact_id,
            feature_count=feature_count,
            label_distribution_json=label_distribution_json,
            excluded_columns_json=excluded_columns_json,
            sequence_length=sequence_length,
            metadata_json={
                **(metadata_json or {}),
                "experiment_id": experiment_id,
                "preprocessing_profile": preprocessing_profile,
                "content_hash_sha256": write_result.content_hash_sha256,
                "file_size_bytes": write_result.file_size_bytes,
                "compression": write_result.compression,
                "write_duration_seconds": write_result.write_duration_seconds,
            },
        )
        return RegisteredModelReadyArtifact(
            data_type=data_type,
            role=role,
            artifact_path=write_result.relative_path,
            catalog_id=int(artifact.id),
            sample_count=write_result.row_count,
            feature_count=feature_count,
        )

    def register_row_batches(
        self,
        repository: ArtifactRepository,
        row_batches: Iterable[list[dict[str, Any]]],
        *,
        columns: list[str],
        schema: pa.Schema | None = None,
        experiment_id: str,
        branch: str,
        preprocessing_profile: str,
        role: str,
        data_type: str,
        file_name: str,
        feature_artifact_id: int | None = None,
        preprocessing_artifact_id: int | None = None,
        feature_count: int | None = None,
        label_distribution_factory: Callable[[], dict[str, Any] | None] | None = None,
        excluded_columns_json: dict[str, Any] | None = None,
        sequence_length: int | None = None,
        metadata_json: dict[str, Any] | None = None,
        resume: bool = False,
        allow_empty: bool = False,
    ) -> RegisteredModelReadyArtifact:
        """Write row batches and register them without materializing all rows."""
        validate_model_ready_data_type(data_type)
        target_path = self.artifact_path(
            experiment_id=experiment_id,
            branch=branch,
            preprocessing_profile=preprocessing_profile,
            role=role,
            file_name=file_name,
        )
        relative_path = _relative_path(target_path, self.storage_root)
        if resume and target_path.exists():
            existing = repository.find_successful_model_ready_artifact(
                branch=branch,
                role=role,
                data_type=data_type,
                artifact_path=relative_path,
                schema_version=MODEL_READY_SCHEMA_VERSION,
            )
            if existing is not None:
                return RegisteredModelReadyArtifact(
                    data_type=data_type,
                    role=role,
                    artifact_path=relative_path,
                    catalog_id=int(existing.id),
                    sample_count=existing.sample_count,
                    feature_count=existing.feature_count,
                    resumed=True,
                )

        write_result = write_model_ready_row_batches(
            row_batches,
            columns=columns,
            schema=schema,
            final_path=target_path,
            storage_root=self.storage_root,
            compression=self.compression,
            validate_x=data_type == "X",
            allow_empty=allow_empty,
        )
        artifact = self._register_write_result(
            repository,
            write_result,
            branch=branch,
            role=role,
            data_type=data_type,
            feature_artifact_id=feature_artifact_id,
            preprocessing_artifact_id=preprocessing_artifact_id,
            feature_count=feature_count,
            label_distribution_json=(
                label_distribution_factory() if label_distribution_factory is not None else None
            ),
            excluded_columns_json=excluded_columns_json,
            sequence_length=sequence_length,
            metadata_json={
                **(metadata_json or {}),
                "experiment_id": experiment_id,
                "preprocessing_profile": preprocessing_profile,
                "content_hash_sha256": write_result.content_hash_sha256,
                "file_size_bytes": write_result.file_size_bytes,
                "compression": write_result.compression,
                "write_duration_seconds": write_result.write_duration_seconds,
            },
        )
        return RegisteredModelReadyArtifact(
            data_type=data_type,
            role=role,
            artifact_path=write_result.relative_path,
            catalog_id=int(artifact.id),
            sample_count=write_result.row_count,
            feature_count=feature_count,
        )

    def _register_write_result(
        self,
        repository: ArtifactRepository,
        write_result: AtomicParquetWriteResult,
        *,
        branch: str,
        role: str,
        data_type: str,
        feature_artifact_id: int | None,
        preprocessing_artifact_id: int | None,
        feature_count: int | None,
        label_distribution_json: dict[str, Any] | None,
        excluded_columns_json: dict[str, Any] | None,
        sequence_length: int | None,
        metadata_json: dict[str, Any],
    ) -> ModelReadyArtifact:
        return repository.register_model_ready_artifact(
            artifact_uid=uuid4(),
            feature_artifact_id=feature_artifact_id,
            preprocessing_artifact_id=preprocessing_artifact_id,
            role=role,
            branch=branch,
            data_type=data_type,
            artifact_path=write_result.relative_path,
            schema_name=MODEL_READY_SCHEMA_NAME,
            schema_version=MODEL_READY_SCHEMA_VERSION,
            sample_count=write_result.row_count,
            feature_count=feature_count,
            label_distribution_json=label_distribution_json,
            excluded_columns_json=excluded_columns_json,
            sequence_length=sequence_length,
            status="SUCCESS",
            metadata_json=metadata_json,
        )


def write_model_ready_rows(
    rows: list[dict[str, Any]],
    *,
    final_path: str | Path,
    storage_root: str | Path,
    compression: str,
    allow_empty: bool = False,
) -> AtomicParquetWriteResult:
    """Write model-ready rows with stable columns and atomic finalization."""
    table = pa.Table.from_pylist(_normalize_rows(rows))
    return write_atomic_parquet_table(
        table,
        final_path=final_path,
        storage_root=storage_root,
        compression=compression,
        allow_empty=allow_empty,
    )


def write_model_ready_row_batches(
    row_batches: Iterable[list[dict[str, Any]]],
    *,
    columns: list[str],
    schema: pa.Schema | None = None,
    final_path: str | Path,
    storage_root: str | Path,
    compression: str,
    validate_x: bool = False,
    allow_empty: bool = False,
) -> AtomicParquetWriteResult:
    """Write model-ready rows from batches with stable columns and atomic finalization."""
    started_at = time.perf_counter()
    resolved_final_path = Path(final_path).expanduser()
    resolved_final_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _temp_path_for(resolved_final_path)
    _cleanup_stale_temps(resolved_final_path)
    writer: pq.ParquetWriter | None = None
    row_count = 0
    column_count = len(columns)
    writer_schema = schema or pa.schema([(column, pa.null()) for column in columns])
    try:
        for rows in row_batches:
            if not rows:
                continue
            normalized = _normalize_rows_to_columns(rows, columns)
            if validate_x:
                validate_no_forbidden_x_columns(normalized)
            table = pa.Table.from_pylist(normalized, schema=writer_schema)
            if writer is None:
                writer = pq.ParquetWriter(temp_path, writer_schema, compression=compression)
            else:
                table = table.cast(writer_schema, safe=False)
            writer.write_table(table)
            row_count += table.num_rows
        if writer is None:
            if not allow_empty:
                raise ParquetWriteError("refusing to write empty model-ready Parquet artifact")
            empty_table = pa.Table.from_pylist([], schema=writer_schema)
            writer = pq.ParquetWriter(temp_path, writer_schema, compression=compression)
            writer.write_table(empty_table)
    except Exception:
        if writer is not None:
            writer.close()
            writer = None
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        if writer is not None:
            writer.close()

    _validate_written_model_ready_file(
        temp_path,
        expected_rows=row_count,
        expected_columns=column_count,
        allow_empty=allow_empty,
    )
    _replace_with_retry(temp_path, resolved_final_path)
    return AtomicParquetWriteResult(
        absolute_path=resolved_final_path,
        relative_path=_relative_path(resolved_final_path, Path(storage_root)),
        row_count=row_count,
        column_count=column_count,
        file_size_bytes=resolved_final_path.stat().st_size,
        content_hash_sha256=sha256_file(resolved_final_path),
        compression=compression,
        write_duration_seconds=time.perf_counter() - started_at,
    )


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    columns = _ordered_columns(rows)
    return [
        {column: _normalize_value(row.get(column)) for column in columns}
        for row in rows
    ]


def _normalize_rows_to_columns(rows: list[dict[str, Any]], columns: list[str]) -> list[dict[str, Any]]:
    return [
        {column: _normalize_value(row.get(column)) for column in columns}
        for row in rows
    ]


def _ordered_columns(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _relative_path(path: Path, storage_root: Path) -> str:
    try:
        return path.relative_to(storage_root).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_segment(value: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError("model-ready path segment must not be empty")
    safe = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in text)
    if safe in {".", ".."} or not safe.strip("."):
        raise ValueError(f"unsafe model-ready path segment: {value!r}")
    return safe


def _temp_path_for(final_path: Path) -> Path:
    return final_path.with_name(f".{final_path.name}.{uuid4().hex}.tmp")


def _cleanup_stale_temps(final_path: Path) -> None:
    for temp_path in final_path.parent.glob(f".{final_path.name}.*.tmp"):
        if temp_path.is_file():
            temp_path.unlink(missing_ok=True)


def _replace_with_retry(temp_path: Path, final_path: Path) -> None:
    delay_seconds = 0.1
    attempts = 6
    for attempt in range(1, attempts + 1):
        try:
            temp_path.replace(final_path)
            return
        except OSError as exc:
            if attempt >= attempts or getattr(exc, "winerror", None) not in {32, 33}:
                raise
            time.sleep(delay_seconds)
            delay_seconds *= 2


def _validate_written_model_ready_file(
    path: Path,
    *,
    expected_rows: int,
    expected_columns: int,
    allow_empty: bool,
) -> None:
    if not path.exists():
        raise ParquetWriteError(f"temporary model-ready Parquet artifact was not created: {path}")
    try:
        metadata = pq.read_metadata(path)
        schema = pq.read_schema(path)
    except Exception as exc:
        raise ParquetWriteError(f"temporary model-ready Parquet artifact is not readable: {path}") from exc
    if metadata.num_rows != expected_rows:
        raise ParquetWriteError(
            f"model-ready Parquet row count mismatch: expected {expected_rows}, got {metadata.num_rows}"
        )
    if metadata.num_rows == 0 and not allow_empty:
        raise ParquetWriteError("refusing to finalize empty model-ready Parquet artifact")
    if len(schema.names) != expected_columns:
        raise ParquetWriteError(
            f"model-ready Parquet column count mismatch: expected {expected_columns}, got {len(schema.names)}"
        )
