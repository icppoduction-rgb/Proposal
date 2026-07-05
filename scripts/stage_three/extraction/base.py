"""Shared contracts for Stage Three feature extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedArtifactInput:
    """Normalized Parquet artifact selected as feature extraction input."""

    artifact_id: int
    dataset_id: int
    role: str
    branch: str
    normalized_path: str
    source_format: str | None = None
    row_count: int | None = None


@dataclass(frozen=True)
class FeatureExtractionArtifact:
    """Feature Parquet artifact emitted by Stage Three extraction."""

    normalized_artifact_id: int
    feature_group: str
    feature_path: str
    parts: list[str]
    rows_read: int
    rows_written: int
    columns_created: list[str]
    missing_ratios: dict[str, float]
    runtime_seconds: float
    peak_rss_gb: float | None


@dataclass(frozen=True)
class FeatureExtractionResult:
    """Serializable result for one feature extraction command."""

    status: str
    branch: str
    role: str
    feature_group: str
    input_normalized_artifacts: list[NormalizedArtifactInput]
    output_feature_artifacts: list[FeatureExtractionArtifact]
    rows_read: int
    rows_written: int
    columns_created: list[str]
    missing_ratios: dict[str, float]
    runtime_seconds: float
    backend_used: str
    peak_rss_gb: float | None
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly payload."""
        return asdict(self)
