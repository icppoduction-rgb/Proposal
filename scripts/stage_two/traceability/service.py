"""Artifact traceability service for Stage Two catalog chains."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import (
    Dataset,
    DatasetFile,
    FeatureArtifact,
    ModelReadyArtifact,
    NormalizedArtifact,
    ParserRun,
)


class TraceabilityError(RuntimeError):
    """Raised when an artifact traceability chain is missing a required link."""


@dataclass(frozen=True)
class TraceabilityChain:
    """Resolved model_ready -> feature -> normalized -> parser_run -> raw file chain."""

    model_ready_artifact: dict[str, Any]
    feature_artifact: dict[str, Any]
    normalized_artifact: dict[str, Any]
    parser_run: dict[str, Any]
    dataset_file: dict[str, Any]
    dataset: dict[str, Any]


class TraceabilityService:
    """Resolve artifact traceability chains from PostgreSQL catalog metadata."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with an externally managed session."""
        self.session = session

    def get_by_model_ready_id(self, artifact_id: int) -> TraceabilityChain:
        """Resolve traceability by model_ready_artifacts.id."""
        artifact = self.session.get(ModelReadyArtifact, artifact_id)
        if artifact is None:
            raise TraceabilityError(f"model_ready_artifact id={artifact_id} was not found")
        return self._resolve(artifact)

    def get_by_model_ready_path(self, artifact_path: str) -> TraceabilityChain:
        """Resolve traceability by model_ready_artifacts.artifact_path."""
        statement = select(ModelReadyArtifact).where(ModelReadyArtifact.artifact_path == artifact_path)
        artifact = self.session.execute(statement).scalar_one_or_none()
        if artifact is None:
            raise TraceabilityError(f"model_ready_artifact path={artifact_path!r} was not found")
        return self._resolve(artifact)

    def _resolve(self, model_ready: ModelReadyArtifact) -> TraceabilityChain:
        feature = self._required_feature(model_ready)
        normalized = self._required_normalized(feature)
        parser_run = self._required_parser_run(normalized)
        dataset_file = self._required_dataset_file(parser_run)
        dataset = self._required_dataset(dataset_file)
        return TraceabilityChain(
            model_ready_artifact=model_ready_metadata(model_ready),
            feature_artifact=feature_metadata(feature),
            normalized_artifact=normalized_metadata(normalized),
            parser_run=parser_run_metadata(parser_run),
            dataset_file=dataset_file_metadata(dataset_file),
            dataset=dataset_metadata(dataset),
        )

    def _required_feature(self, model_ready: ModelReadyArtifact) -> FeatureArtifact:
        if model_ready.feature_artifact_id is None:
            raise TraceabilityError(
                f"model_ready_artifact id={model_ready.id} has no feature_artifact_id"
            )
        feature = self.session.get(FeatureArtifact, model_ready.feature_artifact_id)
        if feature is None:
            raise TraceabilityError(
                f"feature_artifact id={model_ready.feature_artifact_id} linked from model_ready_artifact id={model_ready.id} was not found"
            )
        return feature

    def _required_normalized(self, feature: FeatureArtifact) -> NormalizedArtifact:
        if feature.normalized_artifact_id is None:
            raise TraceabilityError(f"feature_artifact id={feature.id} has no normalized_artifact_id")
        normalized = self.session.get(NormalizedArtifact, feature.normalized_artifact_id)
        if normalized is None:
            raise TraceabilityError(
                f"normalized_artifact id={feature.normalized_artifact_id} linked from feature_artifact id={feature.id} was not found"
            )
        return normalized

    def _required_parser_run(self, normalized: NormalizedArtifact) -> ParserRun:
        parser_run = self.session.get(ParserRun, normalized.parser_run_id)
        if parser_run is None:
            raise TraceabilityError(
                f"parser_run id={normalized.parser_run_id} linked from normalized_artifact id={normalized.id} was not found"
            )
        return parser_run

    def _required_dataset_file(self, parser_run: ParserRun) -> DatasetFile:
        dataset_file = self.session.get(DatasetFile, parser_run.file_id)
        if dataset_file is None:
            raise TraceabilityError(
                f"dataset_file id={parser_run.file_id} linked from parser_run id={parser_run.id} was not found"
            )
        return dataset_file

    def _required_dataset(self, dataset_file: DatasetFile) -> Dataset:
        dataset = self.session.get(Dataset, dataset_file.dataset_id)
        if dataset is None:
            raise TraceabilityError(
                f"dataset id={dataset_file.dataset_id} linked from dataset_file id={dataset_file.id} was not found"
            )
        return dataset


def model_ready_metadata(artifact: ModelReadyArtifact) -> dict[str, Any]:
    """Return serializable model-ready artifact metadata."""
    return {
        "id": artifact.id,
        "artifact_path": artifact.artifact_path,
        "role": artifact.role,
        "branch": artifact.branch,
        "data_type": artifact.data_type,
        "status": artifact.status,
    }


def feature_metadata(artifact: FeatureArtifact) -> dict[str, Any]:
    """Return serializable feature artifact metadata."""
    return {
        "id": artifact.id,
        "feature_path": artifact.feature_path,
        "role": artifact.role,
        "branch": artifact.branch,
        "feature_group": artifact.feature_group,
        "status": artifact.status,
    }


def normalized_metadata(artifact: NormalizedArtifact) -> dict[str, Any]:
    """Return serializable normalized artifact metadata."""
    return {
        "id": artifact.id,
        "normalized_path": artifact.normalized_path,
        "role": artifact.role,
        "branch": artifact.branch,
        "modality": artifact.modality,
        "status": artifact.status,
    }


def parser_run_metadata(parser_run: ParserRun) -> dict[str, Any]:
    """Return serializable parser run metadata."""
    return {
        "id": parser_run.id,
        "parser_name": parser_run.parser_name,
        "parser_version": parser_run.parser_version,
        "status": parser_run.status,
        "rows_read": parser_run.rows_read,
        "rows_parsed": parser_run.rows_parsed,
        "rows_failed": parser_run.rows_failed,
    }


def dataset_file_metadata(dataset_file: DatasetFile) -> dict[str, Any]:
    """Return serializable raw dataset file metadata."""
    metadata = dataset_file.metadata_json or {}
    return {
        "id": dataset_file.id,
        "file_path": dataset_file.file_path,
        "relative_path": dataset_file.relative_path,
        "file_hash_sha256": dataset_file.file_hash_sha256,
        "role": dataset_file.role,
        "branch": dataset_file.branch,
        "source_format": dataset_file.source_format,
        "status": dataset_file.status,
        "metadata_json": metadata,
        "chunk": {
            "is_chunk": "parent_file_id" in metadata or "split_source_file_id" in metadata,
            "parent_file_id": metadata.get("parent_file_id") or metadata.get("split_source_file_id"),
            "chunk_index": metadata.get("chunk_index") or metadata.get("split_part_index"),
            "chunk_path": metadata.get("chunk_path") or dataset_file.file_path,
            "byte_start": metadata.get("byte_start"),
            "byte_end": metadata.get("byte_end"),
            "line_start": metadata.get("line_start"),
            "line_end": metadata.get("line_end"),
            "source_order_preserved": metadata.get("source_order_preserved"),
            "original_source_path": metadata.get("original_source_path") or metadata.get("split_source_file_path"),
        },
    }


def dataset_metadata(dataset: Dataset) -> dict[str, Any]:
    """Return serializable dataset metadata."""
    return {
        "id": dataset.id,
        "name": dataset.name,
        "slug": dataset.slug,
        "role": dataset.role,
        "branch": dataset.branch,
        "source_group": dataset.source_group,
    }
