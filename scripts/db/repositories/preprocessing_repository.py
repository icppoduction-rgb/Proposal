"""Repository for preprocessing artifacts."""

from __future__ import annotations

from typing import Any

from scripts.db.models import PreprocessingArtifact
from scripts.db.repositories.base_repository import BaseRepository


class PreprocessingRepository(BaseRepository[PreprocessingArtifact]):
    """Data access methods for `preprocessing_artifacts`."""

    model = PreprocessingArtifact

    def register_preprocessing_artifact(self, **values: Any) -> PreprocessingArtifact:
        """Register a TRAIN-fitted preprocessing artifact without committing."""
        artifact = PreprocessingArtifact(**values)
        return self.add(artifact)
