"""Typed request objects for Stage Three CLI commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageThreeBaseRequest:
    """Common execution flags shared by Stage Three commands."""

    command: str
    dry_run: bool = False
    resume: bool = False


@dataclass(frozen=True)
class ValidateInputsRequest(StageThreeBaseRequest):
    """Request for validating Stage Two outputs before Stage Three work."""

    branch: str = ""
    role: str = ""


@dataclass(frozen=True)
class BuildFeatureCatalogRequest(StageThreeBaseRequest):
    """Request for creating or validating the machine-readable feature catalog."""

    feature_group: str | None = None


@dataclass(frozen=True)
class ProbeRuntimeBackendRequest(StageThreeBaseRequest):
    """Request for probing Stage Three feature extraction runtime backend."""

    backend: str = "auto"
    profile: str | None = None
    skip_probe: bool = False


@dataclass(frozen=True)
class ExtractFeaturesRequest(StageThreeBaseRequest):
    """Request for extracting feature artifacts from normalized Parquet data."""

    branch: str = ""
    role: str = ""
    feature_group: str = ""
    experiment_id: str | None = None


@dataclass(frozen=True)
class AlignLabelsRequest(StageThreeBaseRequest):
    """Request for aligning labels to feature rows, windows, or sequences."""

    branch: str = ""
    role: str = ""
    label_policy: str = "explicit_only"
    experiment_id: str | None = None


@dataclass(frozen=True)
class BuildSequencesRequest(StageThreeBaseRequest):
    """Request for building sequence/window artifacts."""

    branch: str = ""
    role: str | None = None
    feature_group: str | None = None
    experiment_id: str | None = None


@dataclass(frozen=True)
class BuildModelReadyRequest(StageThreeBaseRequest):
    """Request for assembling X/y/metadata/traceability model-ready artifacts."""

    branch: str = ""
    experiment_id: str = ""
    role: str | None = None
    feature_group: str | None = None
    target: str = "label_binary"
    preprocessing_profile: str = "tree_unscaled"
    include_sequences: bool = False


@dataclass(frozen=True)
class RunQualityChecksRequest(StageThreeBaseRequest):
    """Request for Stage Three quality checks."""

    experiment_id: str = ""
    branch: str | None = None
    role: str | None = None
    feature_group: str | None = None


@dataclass(frozen=True)
class RunLeakageChecksRequest(StageThreeBaseRequest):
    """Request for Stage Three leakage checks."""

    experiment_id: str = ""
    branch: str | None = None
    role: str | None = None
    feature_group: str | None = None


@dataclass(frozen=True)
class TraceArtifactRequest(StageThreeBaseRequest):
    """Request for resolving feature/model-ready artifact lineage."""

    artifact_ref: str | None = None
    experiment_id: str | None = None


@dataclass(frozen=True)
class FinalReportRequest(StageThreeBaseRequest):
    """Request for generating the final Stage Three report."""

    experiment_id: str = ""
    branch: str | None = None
