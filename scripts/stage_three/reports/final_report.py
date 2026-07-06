"""Final Stage Three report generation."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from config import (
    PATH_DATA_STORAGE,
    STAGE_THREE_ACCELERATION_BACKEND,
    STAGE_THREE_BATCH_ROWS,
    STAGE_THREE_DEFAULT_PROFILE,
    STAGE_THREE_DEFAULT_WORKERS,
    STAGE_THREE_FEATURE_CATALOG_PATH,
    STAGE_THREE_HARD_RAM_LIMIT_GB,
    STAGE_THREE_MAX_WORKERS,
    STAGE_THREE_PARQUET_ROW_GROUP_SIZE,
    STAGE_THREE_RESERVED_RAM_GB,
    STAGE_THREE_SOFT_RAM_LIMIT_GB,
)
from scripts.db.models import DataQualityReport, FeatureArtifact, ModelReadyArtifact
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK20_REPORT_FILENAME = "Task20-stage-three-final-report-and-documentation.md"
TASK20_PREVIOUS_REPORT_PATH = "Task19-stage-three-leakage-and-traceability-checks.md"
DOCUMENTATION_FILES = (
    "docs/ru/stage-three/README.md",
    "docs/ru/stage-three/usage_guide.md",
    "docs/ru/stage-three/stage_three_commands.md",
    "docs/ru/stage-three/performance_tuning.md",
    "docs/en/stage-three/README.md",
    "docs/en/stage-three/usage_guide.md",
    "docs/en/stage-three/stage_three_commands.md",
    "docs/en/stage-three/performance_tuning.md",
)
REQUIRED_MODEL_READY_DATA_TYPES = ("X", "y", "metadata", "traceability")
REQUIRED_ROLES = ("TRAIN", "VALIDATION", "TEST")
BLOCKING_ARTIFACT_STATUSES = {"FAILED", "BLOCKED", "BLOCKED_BY_LEAKAGE", "BLOCKED_BY_QUALITY"}
BLOCKING_REPORT_STATUSES = {"FAILED", "BLOCKED"}


@dataclass(frozen=True)
class FinalStageThreeReportResult:
    """Report payload returned by the final Stage Three command."""

    status: str
    stage_four_readiness_status: str
    experiment_id: str
    branch: str | None
    previous_report_path: str
    report_paths: dict[str, str]
    documentation_files: list[str]
    feature_catalog_summary: dict[str, Any]
    stage_two_inputs_summary: dict[str, Any]
    feature_extraction_summary: dict[str, Any]
    label_alignment_summary: dict[str, Any]
    separation_summary: dict[str, Any]
    preprocessing_summary: dict[str, Any]
    class_balance_summary: dict[str, Any]
    sequence_artifact_summary: dict[str, Any]
    model_ready_artifact_summary: dict[str, Any]
    quality_checks_summary: dict[str, Any]
    leakage_checks_summary: dict[str, Any]
    traceability_checks_summary: dict[str, Any]
    runtime_summary: dict[str, Any]
    known_limitations: list[str] = field(default_factory=list)
    readiness_blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly representation."""
        return {
            "status": self.status,
            "stage_four_readiness_status": self.stage_four_readiness_status,
            "experiment_id": self.experiment_id,
            "branch": self.branch,
            "previous_report_path": self.previous_report_path,
            "report_paths": dict(self.report_paths),
            "documentation_files": list(self.documentation_files),
            "feature_catalog_summary": self.feature_catalog_summary,
            "stage_two_inputs_summary": self.stage_two_inputs_summary,
            "feature_extraction_summary": self.feature_extraction_summary,
            "label_alignment_summary": self.label_alignment_summary,
            "separation_summary": self.separation_summary,
            "preprocessing_summary": self.preprocessing_summary,
            "class_balance_summary": self.class_balance_summary,
            "sequence_artifact_summary": self.sequence_artifact_summary,
            "model_ready_artifact_summary": self.model_ready_artifact_summary,
            "quality_checks_summary": self.quality_checks_summary,
            "leakage_checks_summary": self.leakage_checks_summary,
            "traceability_checks_summary": self.traceability_checks_summary,
            "runtime_summary": self.runtime_summary,
            "known_limitations": list(self.known_limitations),
            "readiness_blockers": list(self.readiness_blockers),
        }


def generate_final_stage_three_report(
    session: Session,
    *,
    experiment_id: str,
    branch: str | None = None,
    storage_root: str | Path = PATH_DATA_STORAGE,
) -> FinalStageThreeReportResult:
    """Collect Stage Three catalog state and write RU/EN final reports."""
    model_ready_artifacts = _list_model_ready_artifacts(
        session,
        experiment_id=experiment_id,
        branch=branch,
    )
    feature_artifacts = _linked_feature_artifacts(model_ready_artifacts)
    data_quality_reports = _list_quality_reports(
        session,
        model_ready_artifacts=model_ready_artifacts,
        feature_artifacts=feature_artifacts,
    )
    summaries = _build_summaries(
        experiment_id=experiment_id,
        branch=branch,
        model_ready_artifacts=model_ready_artifacts,
        feature_artifacts=feature_artifacts,
        data_quality_reports=data_quality_reports,
        storage_root=storage_root,
    )
    readiness_status, blockers = _stage_four_readiness(
        model_ready_artifacts,
        data_quality_reports,
    )
    status = "PASS" if readiness_status == "READY_FOR_STAGE_FOUR" else "PARTIAL_SUCCESS"
    paths = build_stage_three_task_report_paths(TASK20_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    result = FinalStageThreeReportResult(
        status=status,
        stage_four_readiness_status=readiness_status,
        experiment_id=experiment_id,
        branch=branch,
        previous_report_path=TASK20_PREVIOUS_REPORT_PATH,
        report_paths=report_paths,
        documentation_files=list(DOCUMENTATION_FILES),
        known_limitations=_known_limitations(),
        readiness_blockers=blockers,
        **summaries,
    )
    save_final_stage_three_reports(result)
    return result


def generate_catalog_unavailable_final_report(
    *,
    experiment_id: str,
    branch: str | None = None,
    error: str,
    storage_root: str | Path = PATH_DATA_STORAGE,
) -> FinalStageThreeReportResult:
    """Write a final report when PostgreSQL catalog state cannot be queried."""
    paths = build_stage_three_task_report_paths(TASK20_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    blocker = f"PostgreSQL catalog is not reachable; final artifact readiness could not be verified: {error}"
    result = FinalStageThreeReportResult(
        status="PARTIAL_SUCCESS",
        stage_four_readiness_status="NOT_READY_FOR_STAGE_FOUR",
        experiment_id=experiment_id,
        branch=branch,
        previous_report_path=TASK20_PREVIOUS_REPORT_PATH,
        report_paths=report_paths,
        documentation_files=list(DOCUMENTATION_FILES),
        feature_catalog_summary=_feature_catalog_summary(),
        stage_two_inputs_summary={
            "status": "UNKNOWN",
            "linked_normalized_artifact_count": 0,
            "reason": "catalog_unavailable",
        },
        feature_extraction_summary={
            "status": "UNKNOWN",
            "feature_artifact_count": 0,
            "reason": "catalog_unavailable",
        },
        label_alignment_summary={"status": "UNKNOWN", "reason": "catalog_unavailable"},
        separation_summary={"status": "UNKNOWN", "reason": "catalog_unavailable"},
        preprocessing_summary={"status": "UNKNOWN", "reason": "catalog_unavailable"},
        class_balance_summary={"status": "UNKNOWN", "reason": "catalog_unavailable"},
        sequence_artifact_summary={"status": "UNKNOWN", "reason": "catalog_unavailable"},
        model_ready_artifact_summary={
            "status": "UNKNOWN",
            "artifact_count": 0,
            "reason": "catalog_unavailable",
        },
        quality_checks_summary={"status": "UNKNOWN", "report_count": 0, "reason": "catalog_unavailable"},
        leakage_checks_summary={"status": "UNKNOWN", "report_count": 0, "reason": "catalog_unavailable"},
        traceability_checks_summary={"status": "UNKNOWN", "report_count": 0, "reason": "catalog_unavailable"},
        runtime_summary=_runtime_summary(
            experiment_id=experiment_id,
            branch=branch,
            storage_root=storage_root,
        ),
        known_limitations=_known_limitations(),
        readiness_blockers=[blocker],
    )
    save_final_stage_three_reports(result)
    return result


def save_final_stage_three_reports(result: FinalStageThreeReportResult) -> FinalStageThreeReportResult:
    """Write RU and EN final Stage Three reports from a prepared payload."""
    ru_path = Path(result.report_paths["ru"])
    en_path = Path(result.report_paths["en"])
    ru_path.parent.mkdir(parents=True, exist_ok=True)
    en_path.parent.mkdir(parents=True, exist_ok=True)
    ru_path.write_text(_render_ru(result), encoding="utf-8")
    en_path.write_text(_render_en(result), encoding="utf-8")
    return result


def _list_model_ready_artifacts(
    session: Session,
    *,
    experiment_id: str,
    branch: str | None,
) -> list[ModelReadyArtifact]:
    statement = (
        select(ModelReadyArtifact)
        .options(
            joinedload(ModelReadyArtifact.feature_artifact).joinedload(FeatureArtifact.normalized_artifact),
            joinedload(ModelReadyArtifact.preprocessing_artifact),
        )
        .where(ModelReadyArtifact.metadata_json["experiment_id"].as_string() == experiment_id)
        .order_by(ModelReadyArtifact.branch.asc(), ModelReadyArtifact.role.asc(), ModelReadyArtifact.data_type.asc())
    )
    if branch is not None:
        statement = statement.where(ModelReadyArtifact.branch == branch)
    return list(session.execute(statement).scalars())


def _linked_feature_artifacts(model_ready_artifacts: list[ModelReadyArtifact]) -> list[FeatureArtifact]:
    by_id: dict[int, FeatureArtifact] = {}
    for artifact in model_ready_artifacts:
        feature_artifact = artifact.feature_artifact
        if feature_artifact is not None:
            by_id[int(feature_artifact.id)] = feature_artifact
    return [by_id[key] for key in sorted(by_id)]


def _list_quality_reports(
    session: Session,
    *,
    model_ready_artifacts: list[ModelReadyArtifact],
    feature_artifacts: list[FeatureArtifact],
) -> list[DataQualityReport]:
    model_ready_ids = [int(artifact.id) for artifact in model_ready_artifacts]
    feature_ids = [int(artifact.id) for artifact in feature_artifacts]
    conditions = []
    if model_ready_ids:
        conditions.append(
            (DataQualityReport.artifact_type == "model_ready")
            & DataQualityReport.artifact_id.in_(model_ready_ids)
        )
    if feature_ids:
        conditions.append(
            (DataQualityReport.artifact_type == "feature")
            & DataQualityReport.artifact_id.in_(feature_ids)
        )
    conditions.append(DataQualityReport.report_path.ilike(f"%{TASK20_PREVIOUS_REPORT_PATH}%"))
    statement = select(DataQualityReport).order_by(DataQualityReport.created_at.desc(), DataQualityReport.id.desc())
    if conditions:
        statement = statement.where(or_(*conditions))
    return list(session.execute(statement).scalars())


def _build_summaries(
    *,
    experiment_id: str,
    branch: str | None,
    model_ready_artifacts: list[ModelReadyArtifact],
    feature_artifacts: list[FeatureArtifact],
    data_quality_reports: list[DataQualityReport],
    storage_root: str | Path,
) -> dict[str, Any]:
    catalog_summary = _feature_catalog_summary()
    return {
        "feature_catalog_summary": catalog_summary,
        "stage_two_inputs_summary": _stage_two_inputs_summary(feature_artifacts),
        "feature_extraction_summary": _feature_extraction_summary(feature_artifacts),
        "label_alignment_summary": _label_alignment_summary(model_ready_artifacts),
        "separation_summary": _separation_summary(model_ready_artifacts),
        "preprocessing_summary": _preprocessing_summary(model_ready_artifacts),
        "class_balance_summary": _class_balance_summary(model_ready_artifacts),
        "sequence_artifact_summary": _sequence_summary(model_ready_artifacts),
        "model_ready_artifact_summary": _model_ready_summary(model_ready_artifacts),
        "quality_checks_summary": _reports_summary(data_quality_reports, include_groups=None, exclude_groups={"leakage", "traceability"}),
        "leakage_checks_summary": _reports_summary(data_quality_reports, include_groups={"leakage"}, exclude_groups=None),
        "traceability_checks_summary": _reports_summary(data_quality_reports, include_groups={"traceability"}, exclude_groups=None),
        "runtime_summary": _runtime_summary(
            experiment_id=experiment_id,
            branch=branch,
            storage_root=storage_root,
        ),
    }


def _feature_catalog_summary() -> dict[str, Any]:
    try:
        catalog = load_feature_catalog(STAGE_THREE_FEATURE_CATALOG_PATH)
    except (OSError, ValueError) as exc:
        return {
            "status": "UNAVAILABLE",
            "path": STAGE_THREE_FEATURE_CATALOG_PATH,
            "error": str(exc),
        }
    groups = catalog.get("feature_groups", {})
    group_items = groups.items() if isinstance(groups, dict) else []
    enabled_groups = [name for name, group in group_items if isinstance(group, dict) and group.get("enabled") is True]
    planned_groups = [name for name, group in group_items if isinstance(group, dict) and group.get("planned") is True]
    feature_count = 0
    if isinstance(groups, dict):
        for group in groups.values():
            if isinstance(group, dict) and isinstance(group.get("features"), list):
                feature_count += len(group["features"])
    return {
        "status": "AVAILABLE",
        "path": STAGE_THREE_FEATURE_CATALOG_PATH,
        "version": str(catalog.get("version", "")),
        "feature_group_count": len(groups) if isinstance(groups, dict) else 0,
        "feature_count": feature_count,
        "enabled_feature_groups": sorted(enabled_groups),
        "planned_feature_groups": sorted(planned_groups),
    }


def _stage_two_inputs_summary(feature_artifacts: list[FeatureArtifact]) -> dict[str, Any]:
    normalized_ids = {
        int(artifact.normalized_artifact_id)
        for artifact in feature_artifacts
        if artifact.normalized_artifact_id is not None
    }
    parser_run_ids = {
        int(artifact.normalized_artifact.parser_run_id)
        for artifact in feature_artifacts
        if artifact.normalized_artifact is not None and artifact.normalized_artifact.parser_run_id is not None
    }
    dataset_ids = {
        int(artifact.dataset_id)
        for artifact in feature_artifacts
        if artifact.dataset_id is not None
    }
    return {
        "linked_normalized_artifact_count": len(normalized_ids),
        "linked_parser_run_count": len(parser_run_ids),
        "linked_dataset_count": len(dataset_ids),
        "normalized_artifact_ids_sample": sorted(normalized_ids)[:20],
        "parser_run_ids_sample": sorted(parser_run_ids)[:20],
    }


def _feature_extraction_summary(feature_artifacts: list[FeatureArtifact]) -> dict[str, Any]:
    return {
        "feature_artifact_count": len(feature_artifacts),
        "by_branch": _count_by(feature_artifacts, "branch"),
        "by_role": _count_by(feature_artifacts, "role"),
        "by_feature_group": _count_by(feature_artifacts, "feature_group"),
        "rows": sum(_optional_int(artifact.row_count) for artifact in feature_artifacts),
        "samples": sum(_optional_int(artifact.sample_count) for artifact in feature_artifacts),
        "max_feature_count": max([_optional_int(artifact.feature_count) for artifact in feature_artifacts] or [0]),
    }


def _label_alignment_summary(model_ready_artifacts: list[ModelReadyArtifact]) -> dict[str, Any]:
    y_artifacts = [artifact for artifact in model_ready_artifacts if artifact.data_type == "y"]
    distributions: dict[str, dict[str, int]] = {}
    for artifact in y_artifacts:
        key = f"{artifact.branch}/{artifact.role}"
        distributions[key] = {
            str(label): int(count)
            for label, count in (artifact.label_distribution_json or {}).items()
            if isinstance(count, int)
        }
    return {
        "y_artifact_count": len(y_artifacts),
        "target_columns": sorted(
            {
                str((artifact.metadata_json or {}).get("target"))
                for artifact in y_artifacts
                if (artifact.metadata_json or {}).get("target")
            }
        ),
        "label_distribution_by_split": distributions,
    }


def _separation_summary(model_ready_artifacts: list[ModelReadyArtifact]) -> dict[str, Any]:
    by_type = _count_by(model_ready_artifacts, "data_type")
    x_artifacts = [artifact for artifact in model_ready_artifacts if artifact.data_type == "X"]
    forbidden_removed = sum(
        len((artifact.excluded_columns_json or {}).get("dropped_columns", []))
        for artifact in x_artifacts
        if isinstance(artifact.excluded_columns_json, dict)
    )
    return {
        "x_artifact_count": by_type.get("X", 0),
        "y_artifact_count": by_type.get("y", 0),
        "metadata_artifact_count": by_type.get("metadata", 0),
        "traceability_artifact_count": by_type.get("traceability", 0),
        "forbidden_or_non_x_columns_removed_count": forbidden_removed,
    }


def _preprocessing_summary(model_ready_artifacts: list[ModelReadyArtifact]) -> dict[str, Any]:
    metadata = [artifact.metadata_json or {} for artifact in model_ready_artifacts]
    return {
        "profiles": sorted({str(item.get("preprocessing_profile")) for item in metadata if item.get("preprocessing_profile")}),
        "fitted_on_role_values": sorted({str(item.get("fitted_on_role")) for item in metadata if item.get("fitted_on_role")}),
        "preprocessing_metadata_artifact_count": sum(
            1 for artifact in model_ready_artifacts if artifact.data_type == "preprocessing_metadata"
        ),
        "linked_preprocessing_artifact_count": len(
            {
                int(artifact.preprocessing_artifact_id)
                for artifact in model_ready_artifacts
                if artifact.preprocessing_artifact_id is not None
            }
        ),
    }


def _class_balance_summary(model_ready_artifacts: list[ModelReadyArtifact]) -> dict[str, Any]:
    y_artifacts = [artifact for artifact in model_ready_artifacts if artifact.data_type == "y"]
    return {
        "class_balance_policy": "report-only/class_weight metadata by default; resampling must affect TRAIN only",
        "validation_test_balancing_allowed": False,
        "label_distribution_by_role": {
            artifact.role: artifact.label_distribution_json or {}
            for artifact in y_artifacts
        },
    }


def _sequence_summary(model_ready_artifacts: list[ModelReadyArtifact]) -> dict[str, Any]:
    sequence_artifacts = [artifact for artifact in model_ready_artifacts if artifact.data_type == "sequence"]
    return {
        "sequence_artifact_count": len(sequence_artifacts),
        "sequence_lengths": sorted(
            {
                int(artifact.sequence_length)
                for artifact in sequence_artifacts
                if artifact.sequence_length is not None
            }
        ),
        "sample_count": sum(_optional_int(artifact.sample_count) for artifact in sequence_artifacts),
    }


def _model_ready_summary(model_ready_artifacts: list[ModelReadyArtifact]) -> dict[str, Any]:
    return {
        "artifact_count": len(model_ready_artifacts),
        "by_status": _count_by(model_ready_artifacts, "status"),
        "by_branch": _count_by(model_ready_artifacts, "branch"),
        "by_role": _count_by(model_ready_artifacts, "role"),
        "by_data_type": _count_by(model_ready_artifacts, "data_type"),
        "sample_count": sum(_optional_int(artifact.sample_count) for artifact in model_ready_artifacts),
        "max_feature_count": max([_optional_int(artifact.feature_count) for artifact in model_ready_artifacts] or [0]),
        "artifact_paths_sample": [artifact.artifact_path for artifact in model_ready_artifacts[:20]],
    }


def _reports_summary(
    reports: list[DataQualityReport],
    *,
    include_groups: set[str] | None,
    exclude_groups: set[str] | None,
) -> dict[str, Any]:
    selected = [
        report
        for report in reports
        if (include_groups is None or report.check_group in include_groups)
        and (exclude_groups is None or report.check_group not in exclude_groups)
    ]
    critical_failures = [
        f"{report.check_group}.{report.check_name} artifact={report.artifact_id}"
        for report in selected
        if report.status in BLOCKING_REPORT_STATUSES and report.severity == "CRITICAL"
    ]
    return {
        "report_count": len(selected),
        "by_status": _count_by(selected, "status"),
        "by_severity": _count_by(selected, "severity"),
        "by_check_group": _count_by(selected, "check_group"),
        "critical_failures": critical_failures,
    }


def _runtime_summary(*, experiment_id: str, branch: str | None, storage_root: str | Path) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "branch": branch or "*",
        "storage_root": str(storage_root),
        "default_profile": STAGE_THREE_DEFAULT_PROFILE,
        "acceleration_backend": STAGE_THREE_ACCELERATION_BACKEND,
        "default_workers": STAGE_THREE_DEFAULT_WORKERS,
        "max_workers": STAGE_THREE_MAX_WORKERS,
        "batch_rows": STAGE_THREE_BATCH_ROWS,
        "parquet_row_group_size": STAGE_THREE_PARQUET_ROW_GROUP_SIZE,
        "reserved_ram_gb": STAGE_THREE_RESERVED_RAM_GB,
        "soft_ram_limit_gb": STAGE_THREE_SOFT_RAM_LIMIT_GB,
        "hard_ram_limit_gb": STAGE_THREE_HARD_RAM_LIMIT_GB,
        "runtime_report": "Task06-feature-extraction-runtime-backend.md",
    }


def _stage_four_readiness(
    model_ready_artifacts: list[ModelReadyArtifact],
    data_quality_reports: list[DataQualityReport],
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not model_ready_artifacts:
        blockers.append("No model-ready artifacts are registered for this experiment_id.")
    by_role_type = {(artifact.role, artifact.data_type) for artifact in model_ready_artifacts}
    for role in REQUIRED_ROLES:
        for data_type in REQUIRED_MODEL_READY_DATA_TYPES:
            if (role, data_type) not in by_role_type:
                blockers.append(f"Missing `{data_type}` model-ready artifact for role `{role}`.")
    blocked_artifacts = [
        int(artifact.id)
        for artifact in model_ready_artifacts
        if artifact.status in BLOCKING_ARTIFACT_STATUSES
    ]
    if blocked_artifacts:
        blockers.append(f"Blocked or failed model-ready artifacts: {blocked_artifacts}.")
    missing_check_groups = _missing_required_check_groups(data_quality_reports)
    if missing_check_groups:
        blockers.append(f"Missing final quality/leakage/traceability check groups: {missing_check_groups}.")
    blocking_reports = [
        int(report.id)
        for report in data_quality_reports
        if report.status in BLOCKING_REPORT_STATUSES and report.severity in {"ERROR", "CRITICAL"}
    ]
    if blocking_reports:
        blockers.append(f"Blocking quality/leakage/traceability report IDs: {blocking_reports}.")
    return ("NOT_READY_FOR_STAGE_FOUR" if blockers else "READY_FOR_STAGE_FOUR", blockers)


def _missing_required_check_groups(reports: list[DataQualityReport]) -> list[str]:
    present = {report.check_group for report in reports}
    required = {"leakage", "traceability"}
    has_quality = any(group not in {"leakage", "traceability"} for group in present)
    missing = sorted(required - present)
    if not has_quality:
        missing.insert(0, "quality")
    return missing


def _known_limitations() -> list[str]:
    return [
        "The final report summarizes the current catalog state; it does not rerun extraction, preprocessing, quality, leakage, or traceability checks.",
        "Stage Four should start only when this report says READY_FOR_STAGE_FOUR for the selected experiment_id.",
        "Stage Three prepares model-ready artifacts but does not train RF/XGBoost/CNN/LSTM models or tune thresholds.",
        "MVP DNS artifacts can be Stage Four-ready independently from the broader Host/Network/Hybrid production expansion.",
        "If previous checks were generated as implementation reports only, production artifact readiness remains NOT_READY until checks are rerun against real catalog artifacts.",
    ]


def _render_ru(result: FinalStageThreeReportResult) -> str:
    return _render(
        result,
        title="Task 20 - stage-three-final-report-and-documentation",
        language="ru",
        labels={
            "executive": "Executive summary",
            "ready": "Готовность к Stage Four",
            "docs": "Созданная/обновленная документация",
            "known": "Known limitations",
            "blockers": "Readiness blockers",
        },
    )


def _render_en(result: FinalStageThreeReportResult) -> str:
    return _render(
        result,
        title="Task 20 - stage-three-final-report-and-documentation",
        language="en",
        labels={
            "executive": "Executive Summary",
            "ready": "Stage Four Readiness",
            "docs": "Documentation Created/Updated",
            "known": "Known Limitations",
            "blockers": "Readiness Blockers",
        },
    )


def _render(
    result: FinalStageThreeReportResult,
    *,
    title: str,
    language: str,
    labels: dict[str, str],
) -> str:
    payload = result.to_dict()
    return (
        f"# {title}\n\n"
        f"- Previous report path: `{result.previous_report_path}`\n"
        f"- Final report path: `{result.report_paths[language]}`\n"
        f"- Experiment ID: `{result.experiment_id}`\n"
        f"- Branch: `{result.branch or '*'}`\n"
        f"- Report status: `{result.status}`\n"
        f"- Stage Four readiness status: `{result.stage_four_readiness_status}`\n\n"
        f"## 1. {labels['executive']}\n\n"
        f"{_executive_summary(result)}\n\n"
        "## 2. Inputs from Stage Two\n\n"
        f"{_json_block(result.stage_two_inputs_summary)}\n\n"
        "## 3. Feature Catalogue Version\n\n"
        f"{_json_block(result.feature_catalog_summary)}\n\n"
        "## 4. Feature Extraction Summary\n\n"
        f"{_json_block(result.feature_extraction_summary)}\n\n"
        "## 5. Label Alignment Summary\n\n"
        f"{_json_block(result.label_alignment_summary)}\n\n"
        "## 6. X/y/metadata/traceability Separation Summary\n\n"
        f"{_json_block(result.separation_summary)}\n\n"
        "## 7. Preprocessing Summary\n\n"
        f"{_json_block(result.preprocessing_summary)}\n\n"
        "## 8. Class Balance Summary\n\n"
        f"{_json_block(result.class_balance_summary)}\n\n"
        "## 9. Sequence Artifact Summary\n\n"
        f"{_json_block(result.sequence_artifact_summary)}\n\n"
        "## 10. Model-ready Artifacts\n\n"
        f"{_json_block(result.model_ready_artifact_summary)}\n\n"
        "## 11. Quality Checks\n\n"
        f"{_json_block(result.quality_checks_summary)}\n\n"
        "## 12. Leakage Checks\n\n"
        f"{_json_block(result.leakage_checks_summary)}\n\n"
        "## 13. Traceability Checks\n\n"
        f"{_json_block(result.traceability_checks_summary)}\n\n"
        "## 14. Runtime and Hardware Utilization Summary\n\n"
        f"{_json_block(result.runtime_summary)}\n\n"
        f"## 15. {labels['known']}\n\n"
        f"{_items(result.known_limitations)}\n\n"
        f"## 16. {labels['ready']}\n\n"
        f"- Stage Four readiness status: `{result.stage_four_readiness_status}`\n"
        f"- Report conclusion: `{result.status}`\n\n"
        f"### {labels['blockers']}\n\n"
        f"{_items(result.readiness_blockers)}\n\n"
        f"### {labels['docs']}\n\n"
        f"{_items(result.documentation_files, code=True)}\n\n"
        "## Machine-readable Details\n\n"
        f"{_json_block(payload)}\n"
    )


def _executive_summary(result: FinalStageThreeReportResult) -> str:
    model_ready_count = result.model_ready_artifact_summary.get("artifact_count", 0)
    feature_count = result.feature_extraction_summary.get("feature_artifact_count", 0)
    return (
        f"Stage Three final report generated for experiment `{result.experiment_id}`. "
        f"The catalog currently contains `{feature_count}` linked feature artifacts and "
        f"`{model_ready_count}` model-ready artifacts in scope. "
        f"Current Stage Four readiness is `{result.stage_four_readiness_status}`."
    )


def _items(values: list[str], *, code: bool = False) -> str:
    if not values:
        return "- `none`"
    if code:
        return "\n".join(f"- `{value}`" for value in values)
    return "\n".join(f"- {value}" for value in values)


def _json_block(value: Any) -> str:
    return f"```json\n{json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)}\n```"


def _count_by(values: list[Any], attribute: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for value in values:
        key = getattr(value, attribute, None)
        counter[str(key) if key is not None else "null"] += 1
    return dict(sorted(counter.items()))


def _optional_int(value: int | None) -> int:
    return int(value) if value is not None else 0
