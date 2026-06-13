"""Registry service for model-ready and preprocessing artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from scripts.db.models import ModelReadyArtifact, PreprocessingArtifact
from scripts.db.repositories import ArtifactRepository, PreprocessingRepository
from scripts.stage_two.model_ready.contracts import (
    MODEL_READY_SCHEMA_NAME,
    MODEL_READY_SCHEMA_VERSION,
    validate_model_ready_data_type,
    validate_preprocessing_fit_role,
    validate_x_columns,
)
from scripts.stage_two.parquet import ParquetArtifactWriter, ParquetWriteResult


@dataclass(frozen=True)
class ModelReadyWriteResult:
    """Model-ready Parquet write result plus registered catalog artifact."""

    write_result: ParquetWriteResult
    artifact: ModelReadyArtifact


class ModelReadyRegistryService:
    """Register model-ready tables, sequences, split indices, and preprocessing objects."""

    def __init__(self, parquet_writer: ParquetArtifactWriter | None = None) -> None:
        """Initialize the service with an optional Parquet writer."""
        self.parquet_writer = parquet_writer or ParquetArtifactWriter()

    def write_table_artifact(
        self,
        repository: ArtifactRepository,
        rows: list[dict[str, Any]],
        *,
        role: str,
        branch: str,
        data_type: str,
        artifact_type: str,
        file_name: str,
        feature_artifact_id: int | None = None,
        preprocessing_artifact_id: int | None = None,
        schema_version: str = MODEL_READY_SCHEMA_VERSION,
        schema_name: str = MODEL_READY_SCHEMA_NAME,
        feature_count: int | None = None,
        label_distribution_json: dict[str, Any] | None = None,
        excluded_columns_json: dict[str, Any] | None = None,
        sequence_length: int | None = None,
        status: str = "SUCCESS",
        metadata_json: dict[str, Any] | None = None,
    ) -> ModelReadyWriteResult:
        """Write a model-ready table to Parquet and register it in catalog."""
        validate_model_ready_data_type(data_type)
        if data_type == "X":
            validate_x_columns(rows)
        write_result = self.parquet_writer.write_model_ready_table(
            rows,
            artifact_type=artifact_type,
            branch=branch,
            role=role,
            schema_version=schema_version,
            file_name=file_name,
        )
        artifact = self.parquet_writer.register_model_ready_artifact(
            repository,
            write_result,
            feature_artifact_id=feature_artifact_id,
            preprocessing_artifact_id=preprocessing_artifact_id,
            role=role,
            branch=branch,
            data_type=data_type,
            schema_name=schema_name,
            schema_version=schema_version,
            feature_count=feature_count if feature_count is not None else infer_table_feature_count(rows, data_type),
            label_distribution_json=label_distribution_json,
            excluded_columns_json=excluded_columns_json,
            sequence_length=sequence_length,
            status=status,
            metadata_json=metadata_json,
        )
        return ModelReadyWriteResult(write_result=write_result, artifact=artifact)

    def register_external_artifact(
        self,
        repository: ArtifactRepository,
        *,
        artifact_path: str | Path,
        role: str,
        branch: str,
        data_type: str,
        feature_artifact_id: int | None = None,
        preprocessing_artifact_id: int | None = None,
        schema_name: str = MODEL_READY_SCHEMA_NAME,
        schema_version: str = MODEL_READY_SCHEMA_VERSION,
        sample_count: int | None = None,
        feature_count: int | None = None,
        label_distribution_json: dict[str, Any] | None = None,
        excluded_columns_json: dict[str, Any] | None = None,
        sequence_length: int | None = None,
        status: str = "SUCCESS",
        metadata_json: dict[str, Any] | None = None,
    ) -> ModelReadyArtifact:
        """Register a pre-written model-ready artifact such as an NPZ sequence file."""
        validate_model_ready_data_type(data_type)
        return repository.register_model_ready_artifact(
            artifact_uid=uuid4(),
            feature_artifact_id=feature_artifact_id,
            preprocessing_artifact_id=preprocessing_artifact_id,
            role=role,
            branch=branch,
            data_type=data_type,
            artifact_path=Path(artifact_path).as_posix(),
            schema_name=schema_name,
            schema_version=schema_version,
            sample_count=sample_count,
            feature_count=feature_count,
            label_distribution_json=label_distribution_json,
            excluded_columns_json=excluded_columns_json,
            sequence_length=sequence_length,
            status=status,
            metadata_json=metadata_json,
        )

    def register_preprocessing_artifact(
        self,
        repository: PreprocessingRepository,
        *,
        branch: str,
        preprocessing_type: str,
        artifact_path: str | Path,
        fitted_on_role: str = "TRAIN",
        feature_group: str | None = None,
        fitted_on_feature_artifact_id: int | None = None,
        schema_version: str = MODEL_READY_SCHEMA_VERSION,
        object_version: str = "v1",
        columns_json: dict[str, Any] | None = None,
        params_json: dict[str, Any] | None = None,
        status: str = "SUCCESS",
    ) -> PreprocessingArtifact:
        """Register a preprocessing object and enforce TRAIN-only fitting."""
        validate_preprocessing_fit_role(fitted_on_role)
        return repository.register_preprocessing_artifact(
            artifact_uid=uuid4(),
            branch=branch,
            feature_group=feature_group,
            preprocessing_type=preprocessing_type,
            artifact_path=Path(artifact_path).as_posix(),
            fitted_on_role=fitted_on_role,
            fitted_on_feature_artifact_id=fitted_on_feature_artifact_id,
            schema_version=schema_version,
            object_version=object_version,
            columns_json=columns_json,
            params_json=params_json,
            status=status,
        )


def infer_table_feature_count(rows: list[dict[str, Any]], data_type: str) -> int | None:
    """Infer feature_count for X tables only."""
    if data_type != "X":
        return None
    if not rows:
        return 0
    return len(set().union(*(row.keys() for row in rows)))
