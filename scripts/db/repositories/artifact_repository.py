"""Repository for artifact registry records."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from scripts.db.models import FeatureArtifact, ModelReadyArtifact, NormalizedArtifact
from scripts.db.repositories.base_repository import BaseRepository


class ArtifactRepository(BaseRepository[NormalizedArtifact]):
    """Data access methods for normalized, feature, and model-ready artifacts."""

    model = NormalizedArtifact

    def register_normalized_artifact(self, **values: Any) -> NormalizedArtifact:
        """Register a normalized artifact without committing."""
        artifact = NormalizedArtifact(**values)
        return self.add(artifact)

    def get_normalized_artifacts_for_run(self, parser_run_id: int) -> list[NormalizedArtifact]:
        """Return normalized artifacts already registered for a parser run."""
        statement = (
            select(NormalizedArtifact)
            .where(NormalizedArtifact.parser_run_id == parser_run_id)
            .order_by(NormalizedArtifact.id.asc())
        )
        return list(self.session.execute(statement).scalars())

    def register_feature_artifact(self, **values: Any) -> FeatureArtifact:
        """Register a feature artifact without committing."""
        artifact = FeatureArtifact(**values)
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def list_successful_feature_artifacts(
        self,
        *,
        branch: str,
        role: str,
        feature_group: str | None = None,
    ) -> list[FeatureArtifact]:
        """Return successful feature artifacts for one branch/role."""
        statement = (
            select(FeatureArtifact)
            .where(
                FeatureArtifact.branch == branch,
                FeatureArtifact.role == role,
                FeatureArtifact.status == "SUCCESS",
            )
            .order_by(FeatureArtifact.id.asc())
        )
        if feature_group is not None:
            statement = statement.where(FeatureArtifact.feature_group == feature_group)
        return list(self.session.execute(statement).scalars())

    def find_successful_feature_artifact(
        self,
        *,
        dataset_id: int,
        normalized_artifact_id: int,
        branch: str,
        role: str,
        feature_group: str,
        schema_version: str,
    ) -> FeatureArtifact | None:
        """Return a successful matching feature artifact for resume checks."""
        statement = (
            select(FeatureArtifact)
            .where(
                FeatureArtifact.dataset_id == dataset_id,
                FeatureArtifact.normalized_artifact_id == normalized_artifact_id,
                FeatureArtifact.branch == branch,
                FeatureArtifact.role == role,
                FeatureArtifact.feature_group == feature_group,
                FeatureArtifact.feature_schema_version == schema_version,
                FeatureArtifact.status == "SUCCESS",
            )
            .order_by(FeatureArtifact.id.desc())
            .limit(1)
        )
        return self.session.execute(statement).scalar_one_or_none()

    def register_model_ready_artifact(self, **values: Any) -> ModelReadyArtifact:
        """Register a model-ready artifact without committing."""
        artifact = ModelReadyArtifact(**values)
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def find_successful_model_ready_artifact(
        self,
        *,
        branch: str,
        role: str,
        data_type: str,
        artifact_path: str,
        schema_version: str,
    ) -> ModelReadyArtifact | None:
        """Return a successful model-ready artifact for resume checks."""
        statement = (
            select(ModelReadyArtifact)
            .where(
                ModelReadyArtifact.branch == branch,
                ModelReadyArtifact.role == role,
                ModelReadyArtifact.data_type == data_type,
                ModelReadyArtifact.artifact_path == artifact_path,
                ModelReadyArtifact.schema_version == schema_version,
                ModelReadyArtifact.status == "SUCCESS",
            )
            .order_by(ModelReadyArtifact.id.desc())
            .limit(1)
        )
        return self.session.execute(statement).scalar_one_or_none()

    def trace_model_ready_to_raw_files(self, model_ready_artifact_id: int) -> list[dict[str, Any]]:
        """Return raw file metadata linked to a model-ready artifact."""
        statement = (
            select(ModelReadyArtifact, FeatureArtifact, NormalizedArtifact)
            .join(FeatureArtifact, ModelReadyArtifact.feature_artifact_id == FeatureArtifact.id)
            .join(
                NormalizedArtifact,
                FeatureArtifact.normalized_artifact_id == NormalizedArtifact.id,
            )
            .where(ModelReadyArtifact.id == model_ready_artifact_id)
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "model_ready_artifact": model_ready,
                "feature_artifact": feature,
                "normalized_artifact": normalized,
                "file_id": normalized.file_id,
                "dataset_id": normalized.dataset_id,
            }
            for model_ready, feature, normalized in rows
        ]
