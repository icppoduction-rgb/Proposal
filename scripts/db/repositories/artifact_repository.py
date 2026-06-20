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

    def register_model_ready_artifact(self, **values: Any) -> ModelReadyArtifact:
        """Register a model-ready artifact without committing."""
        artifact = ModelReadyArtifact(**values)
        self.session.add(artifact)
        self.session.flush()
        return artifact

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
