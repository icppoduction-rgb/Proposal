"""PostgreSQL catalog registration for Stage Three feature artifacts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from scripts.db.models import FeatureArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_three.extraction.artifact_writer import (
    combined_sha256,
    parquet_part_metadata,
)
from scripts.stage_three.extraction.base import (
    FeatureExtractionArtifact,
    FeatureExtractionResult,
    NormalizedArtifactInput,
)


FEATURE_ARTIFACT_SCHEMA_NAME = "feature_artifact"
FEATURE_ARTIFACT_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class SkippedFeatureArtifact:
    """A normalized artifact skipped because a matching catalog row exists."""

    normalized_artifact_id: int
    catalog_artifact_id: int
    feature_path: str
    reason: str


@dataclass(frozen=True)
class FeatureArtifactRegistrationSummary:
    """Registration result for one extraction command."""

    registered_catalog_ids: list[int]
    skipped: list[SkippedFeatureArtifact]


class FeatureArtifactRegistryService:
    """Register feature extraction outputs and provide resume matching."""

    def __init__(self, *, storage_root: str | Path | None = None) -> None:
        self.storage_root = Path(storage_root).expanduser() if storage_root is not None else None

    def filter_resume_inputs(
        self,
        repository: ArtifactRepository,
        artifacts: list[NormalizedArtifactInput],
        *,
        branch: str,
        role: str,
        feature_group: str,
        schema_version: str = FEATURE_ARTIFACT_SCHEMA_VERSION,
        resume: bool,
    ) -> tuple[list[NormalizedArtifactInput], list[SkippedFeatureArtifact]]:
        """Return artifacts still requiring extraction and already-successful skips."""
        if not resume:
            return artifacts, []
        pending: list[NormalizedArtifactInput] = []
        skipped: list[SkippedFeatureArtifact] = []
        for artifact in artifacts:
            existing = repository.find_successful_feature_artifact(
                dataset_id=artifact.dataset_id,
                normalized_artifact_id=artifact.artifact_id,
                branch=branch,
                role=role,
                feature_group=feature_group,
                schema_version=schema_version,
            )
            if existing is None:
                pending.append(artifact)
                continue
            skipped.append(
                SkippedFeatureArtifact(
                    normalized_artifact_id=artifact.artifact_id,
                    catalog_artifact_id=int(existing.id),
                    feature_path=existing.feature_path,
                    reason="matching SUCCESS feature artifact already registered",
                )
            )
        return pending, skipped

    def register_result(
        self,
        repository: ArtifactRepository,
        result: FeatureExtractionResult,
        *,
        schema_name: str = FEATURE_ARTIFACT_SCHEMA_NAME,
        schema_version: str = FEATURE_ARTIFACT_SCHEMA_VERSION,
        skipped: list[SkippedFeatureArtifact] | None = None,
    ) -> tuple[FeatureExtractionResult, FeatureArtifactRegistrationSummary]:
        """Register every output feature artifact and return an annotated result."""
        inputs_by_id = {
            artifact.artifact_id: artifact for artifact in result.input_normalized_artifacts
        }
        registered_outputs: list[FeatureExtractionArtifact] = []
        catalog_ids: list[int] = []
        for output in result.output_feature_artifacts:
            source = inputs_by_id.get(output.normalized_artifact_id)
            if source is None:
                raise ValueError(
                    "cannot register feature artifact without matching normalized input: "
                    f"{output.normalized_artifact_id}"
                )
            artifact = self.register_output(
                repository,
                output,
                source=source,
                branch=result.branch,
                role=result.role,
                feature_group=result.feature_group,
                schema_name=schema_name,
                schema_version=schema_version,
            )
            catalog_ids.append(int(artifact.id))
            registered_outputs.append(
                replace(
                    output,
                    catalog_artifact_id=int(artifact.id),
                    feature_schema_version=schema_version,
                    source_artifact_ids=[source.artifact_id],
                    column_count=len(output.columns_created),
                    artifact_checksum_sha256=(artifact.metadata_json or {}).get(
                        "content_hash_sha256"
                    ),
                )
            )
        skipped_items = skipped or []
        annotated = replace(
            result,
            output_feature_artifacts=registered_outputs,
            registered_catalog_ids=catalog_ids,
            skipped_feature_artifacts=[item.__dict__ for item in skipped_items],
            resume_skipped_count=len(skipped_items),
        )
        return annotated, FeatureArtifactRegistrationSummary(
            registered_catalog_ids=catalog_ids,
            skipped=skipped_items,
        )

    def register_output(
        self,
        repository: ArtifactRepository,
        output: FeatureExtractionArtifact,
        *,
        source: NormalizedArtifactInput,
        branch: str,
        role: str,
        feature_group: str,
        schema_name: str = FEATURE_ARTIFACT_SCHEMA_NAME,
        schema_version: str = FEATURE_ARTIFACT_SCHEMA_VERSION,
        status: str = "SUCCESS",
    ) -> FeatureArtifact:
        """Register one output feature artifact in the PostgreSQL catalog."""
        part_metadata = [
            parquet_part_metadata(path, storage_root=self.storage_root)
            for path in output.parts
        ]
        part_hashes = [str(item["content_hash_sha256"]) for item in part_metadata]
        artifact_checksum = combined_sha256(part_hashes) if part_hashes else ""
        metadata_json = {
            "source_artifact_ids": [source.artifact_id],
            "source_normalized_artifact_ids": [source.artifact_id],
            "source_normalized_path": source.normalized_path,
            "parts": part_metadata,
            "part_count": len(part_metadata),
            "column_count": len(output.columns_created),
            "content_hash_sha256": artifact_checksum,
            "feature_schema_version": schema_version,
            "runtime_stats": output.runtime_stats,
            "warnings": output.warnings,
        }
        return repository.register_feature_artifact(
            dataset_id=source.dataset_id,
            normalized_artifact_id=source.artifact_id,
            role=role,
            branch=branch,
            feature_group=feature_group,
            feature_path=_catalog_feature_path(output.feature_path, self.storage_root),
            feature_schema_name=schema_name,
            feature_schema_version=schema_version,
            row_count=output.rows_written,
            sample_count=output.rows_written,
            feature_count=len(output.columns_created),
            entity_count=None,
            window_size_seconds=None,
            window_step_seconds=None,
            label_distribution_json=None,
            excluded_columns_json=None,
            status=status,
            metadata_json=metadata_json,
        )


def _catalog_feature_path(path: str, storage_root: Path | None) -> str:
    resolved = Path(path).expanduser()
    if storage_root is None:
        return resolved.as_posix()
    try:
        return resolved.relative_to(storage_root).as_posix()
    except ValueError:
        return resolved.as_posix()
