"""Trace Stage Three model-ready artifacts back to raw catalog sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
from scripts.stage_three.quality.common import FAIL, PASS, QualityCheckRecord, fail_check, pass_check


TRACEABILITY_BLOCKING_STATUS = "BLOCKED_BY_QUALITY"


@dataclass(frozen=True)
class TraceabilityChain:
    """Resolved lineage chain for one model-ready artifact."""

    status: str
    model_ready_artifact_id: int
    feature_artifact_id: int | None = None
    normalized_artifact_id: int | None = None
    parser_run_id: int | None = None
    dataset_file_id: int | None = None
    dataset_id: int | None = None
    raw_source_path: str | None = None
    missing_links: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a report-friendly representation."""
        return asdict(self)


def trace_model_ready_artifact(
    session: Session,
    model_ready_artifact_id: int,
    *,
    apply_blocking_status: bool = False,
) -> TraceabilityChain:
    """Resolve one model-ready artifact lineage chain through catalog FKs."""
    row = session.execute(
        select(
            ModelReadyArtifact,
            FeatureArtifact,
            NormalizedArtifact,
            ParserRun,
            DatasetFile,
            Dataset,
        )
        .outerjoin(FeatureArtifact, ModelReadyArtifact.feature_artifact_id == FeatureArtifact.id)
        .outerjoin(NormalizedArtifact, FeatureArtifact.normalized_artifact_id == NormalizedArtifact.id)
        .outerjoin(ParserRun, NormalizedArtifact.parser_run_id == ParserRun.id)
        .outerjoin(DatasetFile, NormalizedArtifact.file_id == DatasetFile.id)
        .outerjoin(Dataset, NormalizedArtifact.dataset_id == Dataset.id)
        .where(ModelReadyArtifact.id == model_ready_artifact_id)
    ).first()
    if row is None:
        return TraceabilityChain(
            status=FAIL,
            model_ready_artifact_id=model_ready_artifact_id,
            missing_links=["model_ready_artifact"],
        )
    model_ready, feature, normalized, parser_run, dataset_file, dataset = row
    missing = _missing_links(model_ready, feature, normalized, parser_run, dataset_file, dataset)
    if missing and apply_blocking_status and model_ready.status == "SUCCESS":
        model_ready.status = TRACEABILITY_BLOCKING_STATUS
    return TraceabilityChain(
        status=FAIL if missing else PASS,
        model_ready_artifact_id=int(model_ready.id),
        feature_artifact_id=int(feature.id) if feature is not None else None,
        normalized_artifact_id=int(normalized.id) if normalized is not None else None,
        parser_run_id=int(parser_run.id) if parser_run is not None else None,
        dataset_file_id=int(dataset_file.id) if dataset_file is not None else None,
        dataset_id=int(dataset.id) if dataset is not None else None,
        raw_source_path=dataset_file.file_path if dataset_file is not None else None,
        missing_links=missing,
        details={
            "model_ready": _artifact_details(model_ready),
            "feature": _feature_details(feature),
            "normalized": _normalized_details(normalized),
            "parser_run": _parser_run_details(parser_run),
            "dataset_file": _dataset_file_details(dataset_file),
            "dataset": _dataset_details(dataset),
        },
    )


def trace_model_ready_artifacts(
    session: Session,
    artifact_ids: list[int],
    *,
    apply_blocking_status: bool = False,
) -> list[TraceabilityChain]:
    """Resolve multiple model-ready artifact lineage chains."""
    return [
        trace_model_ready_artifact(
            session,
            artifact_id,
            apply_blocking_status=apply_blocking_status,
        )
        for artifact_id in artifact_ids
    ]


def traceability_checks_for_artifacts(
    session: Session,
    model_ready_artifacts: list[ModelReadyArtifact],
    *,
    apply_blocking_status: bool = False,
) -> tuple[list[QualityCheckRecord], list[TraceabilityChain]]:
    """Return quality records and chain payloads for model-ready artifacts."""
    records: list[QualityCheckRecord] = []
    chains: list[TraceabilityChain] = []
    for artifact in model_ready_artifacts:
        chain = trace_model_ready_artifact(
            session,
            int(artifact.id),
            apply_blocking_status=apply_blocking_status,
        )
        chains.append(chain)
        if chain.status == FAIL:
            records.append(
                fail_check(
                    check_group="traceability",
                    check_name="model_ready_to_raw_chain",
                    artifact_type="model_ready",
                    artifact_id=int(artifact.id),
                    message="traceability chain is missing required catalog links",
                    blocking=True,
                    schema_mismatch_count=len(chain.missing_links),
                    details=chain.to_dict(),
                )
            )
        else:
            records.append(
                pass_check(
                    check_group="traceability",
                    check_name="model_ready_to_raw_chain",
                    artifact_type="model_ready",
                    artifact_id=int(artifact.id),
                    message="traceability chain resolves to raw source",
                    details=chain.to_dict(),
                )
            )
    return records, chains


def _missing_links(
    model_ready: ModelReadyArtifact,
    feature: FeatureArtifact | None,
    normalized: NormalizedArtifact | None,
    parser_run: ParserRun | None,
    dataset_file: DatasetFile | None,
    dataset: Dataset | None,
) -> list[str]:
    missing: list[str] = []
    if model_ready.feature_artifact_id is None or feature is None:
        missing.append("feature_artifact")
    if feature is None or feature.normalized_artifact_id is None or normalized is None:
        missing.append("normalized_artifact")
    if normalized is None or parser_run is None:
        missing.append("parser_run")
    if normalized is None or dataset_file is None:
        missing.append("dataset_file")
    if normalized is None or dataset is None:
        missing.append("dataset")
    if dataset_file is None or not dataset_file.file_path:
        missing.append("raw_source")
    return missing


def _artifact_details(artifact: ModelReadyArtifact) -> dict[str, Any]:
    return {
        "id": int(artifact.id),
        "role": artifact.role,
        "branch": artifact.branch,
        "data_type": artifact.data_type,
        "artifact_path": artifact.artifact_path,
        "status": artifact.status,
    }


def _feature_details(artifact: FeatureArtifact | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    return {
        "id": int(artifact.id),
        "role": artifact.role,
        "branch": artifact.branch,
        "feature_group": artifact.feature_group,
        "feature_path": artifact.feature_path,
        "status": artifact.status,
    }


def _normalized_details(artifact: NormalizedArtifact | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    return {
        "id": int(artifact.id),
        "role": artifact.role,
        "branch": artifact.branch,
        "normalized_path": artifact.normalized_path,
        "status": artifact.status,
    }


def _parser_run_details(parser_run: ParserRun | None) -> dict[str, Any] | None:
    if parser_run is None:
        return None
    return {
        "id": int(parser_run.id),
        "parser_name": parser_run.parser_name,
        "parser_version": parser_run.parser_version,
        "status": parser_run.status,
    }


def _dataset_file_details(dataset_file: DatasetFile | None) -> dict[str, Any] | None:
    if dataset_file is None:
        return None
    return {
        "id": int(dataset_file.id),
        "role": dataset_file.role,
        "branch": dataset_file.branch,
        "file_path": dataset_file.file_path,
        "file_name": dataset_file.file_name,
        "status": dataset_file.status,
    }


def _dataset_details(dataset: Dataset | None) -> dict[str, Any] | None:
    if dataset is None:
        return None
    return {
        "id": int(dataset.id),
        "name": dataset.name,
        "slug": dataset.slug,
        "role": dataset.role,
        "branch": dataset.branch,
    }
