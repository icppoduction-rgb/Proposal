"""Stage Three model-ready Parquet writer and catalog registration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import pyarrow as pa

from config import PARQUET_MODEL_READY_RELATIVE, PATH_DATA_STORAGE, STAGE_TWO_PARQUET_COMPRESSION
from scripts.db.models import ModelReadyArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_three.extraction.artifact_writer import AtomicParquetWriteResult, write_atomic_parquet_table
from scripts.stage_three.model_ready.separator import validate_no_forbidden_x_columns
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


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    columns = _ordered_columns(rows)
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
