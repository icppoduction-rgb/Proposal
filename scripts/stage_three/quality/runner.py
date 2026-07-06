"""Orchestrate Stage Three quality checks and catalog registration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import FeatureArtifact, ModelReadyArtifact, PreprocessingArtifact
from scripts.db.repositories import DataQualityRepository
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.quality.common import (
    FAIL,
    QualityCheckRecord,
    overall_status,
    register_quality_records,
)
from scripts.stage_three.quality.feature_quality import run_feature_quality_checks
from scripts.stage_three.quality.model_ready_quality import run_model_ready_quality_checks
from scripts.stage_three.quality.preprocessing_quality import run_preprocessing_quality_checks
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK18_REPORT_FILENAME = "Task18-stage-three-quality-checks.md"
TASK18_PREVIOUS_REPORT_PATH = "Task17-model-ready-builder.md"


@dataclass(frozen=True)
class StageThreeQualityResult:
    """Stage Three quality check result for CLI and reports."""

    status: str
    experiment_id: str
    branch: str | None
    role: str | None
    feature_group: str | None
    feature_artifact_count: int
    model_ready_artifact_count: int
    preprocessing_artifact_count: int
    checks: list[QualityCheckRecord]
    blocking_issues: list[str] = field(default_factory=list)
    quality_report_ids: list[int] = field(default_factory=list)
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly payload."""
        return {
            "status": self.status,
            "experiment_id": self.experiment_id,
            "branch": self.branch,
            "role": self.role,
            "feature_group": self.feature_group,
            "feature_artifact_count": self.feature_artifact_count,
            "model_ready_artifact_count": self.model_ready_artifact_count,
            "preprocessing_artifact_count": self.preprocessing_artifact_count,
            "checks": [record.to_dict() for record in self.checks],
            "blocking_issues": list(self.blocking_issues),
            "quality_report_ids": list(self.quality_report_ids),
            "report_paths": dict(self.report_paths),
        }


def run_stage_three_quality_checks(
    session: Session,
    *,
    experiment_id: str,
    storage_root: str | Path,
    branch: str | None = None,
    role: str | None = None,
    feature_group: str | None = None,
) -> StageThreeQualityResult:
    """Run feature, preprocessing, and model-ready quality checks."""
    model_ready_artifacts = _list_model_ready_artifacts(
        session,
        experiment_id=experiment_id,
        branch=branch,
        role=role,
    )
    feature_artifacts = _list_feature_artifacts(
        session,
        model_ready_artifacts=model_ready_artifacts,
        branch=branch,
        role=role,
        feature_group=feature_group,
    )
    preprocessing_artifacts = _list_preprocessing_artifacts(
        session,
        model_ready_artifacts=model_ready_artifacts,
        branch=branch,
        feature_group=feature_group,
    )
    catalog = load_feature_catalog()
    checks: list[QualityCheckRecord] = []
    checks.extend(
        run_feature_quality_checks(
            feature_artifacts,
            storage_root=storage_root,
            feature_catalog=catalog,
        )
    )
    checks.extend(
        run_preprocessing_quality_checks(
            preprocessing_artifacts,
            storage_root=storage_root,
        )
    )
    target = _target_from_model_ready_metadata(model_ready_artifacts)
    checks.extend(
        run_model_ready_quality_checks(
            model_ready_artifacts,
            storage_root=storage_root,
            target=target,
        )
    )
    report_paths = build_stage_three_task_report_paths(TASK18_REPORT_FILENAME, create_dirs=True)
    report_path_map = {"ru": str(report_paths.ru), "en": str(report_paths.en)}
    checks = register_quality_records(
        DataQualityRepository(session),
        checks,
        report_path=str(report_paths.en),
        report_paths=report_path_map,
    )
    blocking_issues = [
        f"{record.check_group}.{record.check_name}: {record.message}"
        for record in checks
        if record.status == FAIL and record.blocking
    ]
    return StageThreeQualityResult(
        status=overall_status(checks),
        experiment_id=experiment_id,
        branch=branch,
        role=role,
        feature_group=feature_group,
        feature_artifact_count=len(feature_artifacts),
        model_ready_artifact_count=len(model_ready_artifacts),
        preprocessing_artifact_count=len(preprocessing_artifacts),
        checks=checks,
        blocking_issues=blocking_issues,
        quality_report_ids=[
            int(record.quality_report_id)
            for record in checks
            if record.quality_report_id is not None
        ],
        report_paths=report_path_map,
    )


def _list_feature_artifacts(
    session: Session,
    *,
    model_ready_artifacts: list[ModelReadyArtifact],
    branch: str | None,
    role: str | None,
    feature_group: str | None,
) -> list[FeatureArtifact]:
    linked_ids = sorted(
        {
            int(artifact.feature_artifact_id)
            for artifact in model_ready_artifacts
            if artifact.feature_artifact_id is not None
        }
    )
    if not linked_ids:
        return []
    statement = (
        select(FeatureArtifact)
        .where(FeatureArtifact.status == "SUCCESS")
        .order_by(FeatureArtifact.id.asc())
    )
    statement = statement.where(FeatureArtifact.id.in_(linked_ids))
    if branch is not None:
        statement = statement.where(FeatureArtifact.branch == branch)
    if role is not None:
        statement = statement.where(FeatureArtifact.role == role)
    if feature_group is not None:
        statement = statement.where(FeatureArtifact.feature_group == feature_group)
    return list(session.execute(statement).scalars())


def _list_model_ready_artifacts(
    session: Session,
    *,
    experiment_id: str,
    branch: str | None,
    role: str | None,
) -> list[ModelReadyArtifact]:
    statement = (
        select(ModelReadyArtifact)
        .where(
            ModelReadyArtifact.status == "SUCCESS",
            ModelReadyArtifact.metadata_json["experiment_id"].as_string() == experiment_id,
        )
        .order_by(ModelReadyArtifact.role.asc(), ModelReadyArtifact.data_type.asc(), ModelReadyArtifact.id.asc())
    )
    if branch is not None:
        statement = statement.where(ModelReadyArtifact.branch == branch)
    if role is not None:
        statement = statement.where(ModelReadyArtifact.role == role)
    return list(session.execute(statement).scalars())


def _list_preprocessing_artifacts(
    session: Session,
    *,
    model_ready_artifacts: list[ModelReadyArtifact],
    branch: str | None,
    feature_group: str | None,
) -> list[PreprocessingArtifact]:
    linked_ids = sorted(
        {
            int(artifact.preprocessing_artifact_id)
            for artifact in model_ready_artifacts
            if artifact.preprocessing_artifact_id is not None
        }
    )
    if not linked_ids:
        return []
    statement = (
        select(PreprocessingArtifact)
        .where(
            PreprocessingArtifact.status == "SUCCESS",
            PreprocessingArtifact.id.in_(linked_ids),
        )
        .order_by(PreprocessingArtifact.id.asc())
    )
    if branch is not None:
        statement = statement.where(PreprocessingArtifact.branch == branch)
    if feature_group is not None:
        statement = statement.where(PreprocessingArtifact.feature_group == feature_group)
    return list(session.execute(statement).scalars())


def _target_from_model_ready_metadata(model_ready_artifacts: list[ModelReadyArtifact]) -> str:
    for artifact in model_ready_artifacts:
        metadata = artifact.metadata_json or {}
        target = metadata.get("target")
        if isinstance(target, str) and target.strip():
            return target.strip()
    return "label_binary"
