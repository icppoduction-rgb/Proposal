"""Placeholder feature artifact writer and registrar for Stage Two."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.db.models import FeatureArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_two.features.contracts import (
    FEATURE_SCHEMA_NAME,
    FEATURE_SCHEMA_VERSION,
    X_EXCLUDED_COLUMNS,
    excluded_columns_payload,
    validate_feature_group,
)
from scripts.stage_two.parquet import ParquetArtifactWriter, ParquetWriteResult


@dataclass(frozen=True)
class FeatureArtifactWriteResult:
    """Feature Parquet write result plus registered catalog artifact."""

    write_result: ParquetWriteResult
    artifact: FeatureArtifact


class FeatureArtifactWriter:
    """Write prepared feature rows and register feature artifact metadata."""

    def __init__(self, parquet_writer: ParquetArtifactWriter | None = None) -> None:
        """Initialize the writer with an optional Parquet writer."""
        self.parquet_writer = parquet_writer or ParquetArtifactWriter()

    def write_and_register(
        self,
        repository: ArtifactRepository,
        rows: list[dict[str, Any]],
        *,
        dataset_id: int,
        dataset_slug: str,
        role: str,
        branch: str,
        feature_group: str,
        normalized_artifact_id: int | None = None,
        schema_version: str = FEATURE_SCHEMA_VERSION,
        run_id: str | int | None = None,
        feature_schema_name: str = FEATURE_SCHEMA_NAME,
        sample_count: int | None = None,
        feature_count: int | None = None,
        entity_count: int | None = None,
        window_size_seconds: int | None = None,
        window_step_seconds: int | None = None,
        label_distribution_json: dict[str, Any] | None = None,
        extra_excluded_columns: list[str] | tuple[str, ...] | None = None,
        metadata_json: dict[str, Any] | None = None,
        status: str = "SUCCESS",
    ) -> FeatureArtifactWriteResult:
        """Write feature rows to Parquet and register the feature artifact."""
        validate_feature_group(feature_group)
        write_result = self.parquet_writer.write_features(
            rows,
            feature_group=feature_group,
            role=role,
            dataset_slug=dataset_slug,
            schema_version=schema_version,
            run_id=run_id,
        )
        resolved_feature_count = feature_count
        if resolved_feature_count is None:
            resolved_feature_count = infer_feature_count(rows, extra_excluded_columns)
        artifact = self.parquet_writer.register_feature_artifact(
            repository,
            write_result,
            dataset_id=dataset_id,
            normalized_artifact_id=normalized_artifact_id,
            role=role,
            branch=branch,
            feature_group=feature_group,
            feature_schema_name=feature_schema_name,
            feature_schema_version=schema_version,
            sample_count=sample_count if sample_count is not None else write_result.row_count,
            feature_count=resolved_feature_count,
            entity_count=entity_count,
            window_size_seconds=window_size_seconds,
            window_step_seconds=window_step_seconds,
            label_distribution_json=label_distribution_json,
            excluded_columns_json=excluded_columns_payload(extra_excluded_columns),
            status=status,
            metadata_json=metadata_json,
        )
        return FeatureArtifactWriteResult(write_result=write_result, artifact=artifact)


def infer_feature_count(
    rows: list[dict[str, Any]],
    extra_excluded_columns: list[str] | tuple[str, ...] | None = None,
) -> int:
    """Infer feature column count from rows by excluding label/source leakage columns."""
    if not rows:
        return 0
    excluded = set(X_EXCLUDED_COLUMNS)
    excluded.update(extra_excluded_columns or ())
    columns = set().union(*(row.keys() for row in rows))
    return len([column for column in columns if column not in excluded])
