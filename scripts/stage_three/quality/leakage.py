"""Stage Three leakage checks over model-ready artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pyarrow as pa
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import FeatureArtifact, ModelReadyArtifact, PreprocessingArtifact
from scripts.db.repositories import DataQualityRepository
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.quality.common import (
    FAIL,
    QualityCheckRecord,
    duckdb_scalar,
    overall_status,
    parquet_paths_from_catalog_path,
    parquet_row_count,
    parquet_schema,
    pass_check,
    quoted_identifier,
    register_quality_records,
    fail_check,
)
from scripts.stage_three.quality.traceability import TraceabilityChain, traceability_checks_for_artifacts
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK19_REPORT_FILENAME = "Task19-stage-three-leakage-and-traceability-checks.md"
TASK19_PREVIOUS_REPORT_PATH = "Task18-stage-three-quality-checks.md"
LEAKAGE_BLOCKING_STATUS = "BLOCKED_BY_LEAKAGE"

CRITICAL_X_FORBIDDEN_COLUMNS = frozenset(
    {
        *FORBIDDEN_X_COLUMNS,
        "source_file",
        "source_path",
        "scenario_name",
        "dataset_name",
        "dataset_role",
        "parser_name",
        "parser_version",
        "raw_fields_json",
        "metadata_json",
    }
)
@dataclass(frozen=True)
class StageThreeLeakageResult:
    """Stage Three leakage/traceability result for CLI and reports."""

    status: str
    experiment_id: str
    branch: str | None
    role: str | None
    feature_group: str | None
    checks: list[QualityCheckRecord]
    traceability_chains: list[TraceabilityChain]
    blocked_artifact_ids: list[int] = field(default_factory=list)
    missing_links: list[str] = field(default_factory=list)
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
            "checks": [record.to_dict() for record in self.checks],
            "traceability_chains": [chain.to_dict() for chain in self.traceability_chains],
            "blocked_artifact_ids": list(self.blocked_artifact_ids),
            "missing_links": list(self.missing_links),
            "quality_report_ids": list(self.quality_report_ids),
            "report_paths": dict(self.report_paths),
        }


def run_stage_three_leakage_checks(
    session: Session,
    *,
    experiment_id: str,
    storage_root: str | Path,
    branch: str | None = None,
    role: str | None = None,
    feature_group: str | None = None,
    apply_blocking_status: bool = True,
) -> StageThreeLeakageResult:
    """Run Stage Three leakage and traceability checks and register DB reports."""
    model_ready_artifacts = _list_model_ready_artifacts(
        session,
        experiment_id=experiment_id,
        branch=branch,
        role=role,
        feature_group=feature_group,
    )
    preprocessing_artifacts = _list_preprocessing_artifacts(
        session,
        branch=branch,
        feature_group=feature_group,
    )
    checks: list[QualityCheckRecord] = []
    blocked_artifact_ids: set[int] = set()
    for artifact in model_ready_artifacts:
        artifact_checks = _check_model_ready_artifact_for_leakage(
            artifact,
            storage_root=storage_root,
        )
        checks.extend(artifact_checks)
        if any(check.status == FAIL and check.blocking for check in artifact_checks):
            blocked_artifact_ids.add(int(artifact.id))
            if apply_blocking_status and artifact.status == "SUCCESS":
                artifact.status = LEAKAGE_BLOCKING_STATUS
    checks.extend(_check_preprocessing_fit_role(preprocessing_artifacts))
    for check in checks:
        if check.check_name == "preprocessing_fitted_only_on_train" and check.status == FAIL:
            for artifact_id in check.details.get("artifact_ids", []):
                blocked_artifact_ids.add(int(artifact_id))
    traceability_records, chains = traceability_checks_for_artifacts(
        session,
        model_ready_artifacts,
        apply_blocking_status=apply_blocking_status,
    )
    checks.extend(traceability_records)
    for record in traceability_records:
        if record.status == FAIL and record.blocking and record.artifact_id is not None:
            blocked_artifact_ids.add(record.artifact_id)

    report_paths = build_stage_three_task_report_paths(TASK19_REPORT_FILENAME, create_dirs=True)
    report_path_map = {"ru": str(report_paths.ru), "en": str(report_paths.en)}
    checks = register_quality_records(
        DataQualityRepository(session),
        checks,
        report_path=str(report_paths.en),
        report_paths=report_path_map,
    )
    return StageThreeLeakageResult(
        status=overall_status(checks),
        experiment_id=experiment_id,
        branch=branch,
        role=role,
        feature_group=feature_group,
        checks=checks,
        traceability_chains=chains,
        blocked_artifact_ids=sorted(blocked_artifact_ids),
        missing_links=sorted(
            {
                link
                for chain in chains
                for link in chain.missing_links
            }
        ),
        quality_report_ids=[
            int(record.quality_report_id)
            for record in checks
            if record.quality_report_id is not None
        ],
        report_paths=report_path_map,
    )


def check_model_ready_artifact_for_leakage(
    artifact: ModelReadyArtifact,
    *,
    storage_root: str | Path,
) -> list[QualityCheckRecord]:
    """Run leakage checks for one model-ready artifact."""
    return _check_model_ready_artifact_for_leakage(artifact, storage_root=storage_root)


def _check_model_ready_artifact_for_leakage(
    artifact: ModelReadyArtifact,
    *,
    storage_root: str | Path,
) -> list[QualityCheckRecord]:
    if artifact.data_type != "X":
        return []
    artifact_id = int(artifact.id)
    paths = parquet_paths_from_catalog_path(artifact.artifact_path, storage_root=storage_root)
    if not paths:
        return [
            fail_check(
                check_group="leakage",
                check_name="x_artifact_readable",
                artifact_type="model_ready",
                artifact_id=artifact_id,
                message="model-ready X artifact path does not resolve to Parquet files",
                details={"artifact_path": artifact.artifact_path},
            )
        ]
    schema = parquet_schema(paths)
    row_count = parquet_row_count(paths)
    columns = list(schema.names)
    records = [
        _check_forbidden_columns(artifact_id, columns, row_count),
        _check_test_rows_absent_from_train(artifact, paths, columns, row_count),
        _check_absolute_paths_absent(artifact_id, paths, schema, row_count),
        _check_test_usage_metadata_absent(artifact, artifact_id),
        _check_validation_test_balancing_absent(artifact, artifact_id),
    ]
    return records


def _check_forbidden_columns(
    artifact_id: int,
    columns: list[str],
    row_count: int,
) -> QualityCheckRecord:
    forbidden = sorted(
        column
        for column in columns
        if column in CRITICAL_X_FORBIDDEN_COLUMNS or column.startswith("label_")
    )
    if forbidden:
        return fail_check(
            check_group="leakage",
            check_name="x_forbidden_columns",
            artifact_type="model_ready",
            artifact_id=artifact_id,
            message="model-ready X contains label/source/parser/metadata leakage columns",
            rows_total=row_count,
            rows_failed=row_count,
            leakage_issue_count=len(forbidden),
            details={"forbidden_columns": forbidden},
        )
    return pass_check(
        check_group="leakage",
        check_name="x_forbidden_columns",
        artifact_type="model_ready",
        artifact_id=artifact_id,
        message="model-ready X contains no forbidden leakage columns",
        rows_total=row_count,
        details={"checked_columns": columns},
    )


def _check_test_rows_absent_from_train(
    artifact: ModelReadyArtifact,
    paths: list[Path],
    columns: list[str],
    row_count: int,
) -> QualityCheckRecord:
    if artifact.role != "TRAIN":
        return pass_check(
            check_group="leakage",
            check_name="test_rows_absent_from_train",
            artifact_type="model_ready",
            artifact_id=int(artifact.id),
            message="artifact is not TRAIN; TEST-in-TRAIN check is not applicable",
            rows_total=row_count,
            details={"role": artifact.role},
        )
    role_columns = [column for column in ("dataset_role", "role", "split_role") if column in columns]
    if not role_columns:
        return pass_check(
            check_group="leakage",
            check_name="test_rows_absent_from_train",
            artifact_type="model_ready",
            artifact_id=int(artifact.id),
            message="TRAIN X has no role columns; TEST row contamination is not present in X columns",
            rows_total=row_count,
            details={"role": artifact.role, "role_columns": []},
        )
    expressions = " + ".join(
        f"SUM(CASE WHEN upper(CAST({quoted_identifier(column)} AS VARCHAR)) = 'TEST' THEN 1 ELSE 0 END)"
        for column in role_columns
    )
    test_count = int(duckdb_scalar(paths, expressions))
    if test_count:
        return fail_check(
            check_group="leakage",
            check_name="test_rows_absent_from_train",
            artifact_type="model_ready",
            artifact_id=int(artifact.id),
            message="TRAIN X contains rows marked as TEST",
            rows_total=row_count,
            rows_failed=test_count,
            leakage_issue_count=test_count,
            details={"role_columns": role_columns},
        )
    return pass_check(
        check_group="leakage",
        check_name="test_rows_absent_from_train",
        artifact_type="model_ready",
        artifact_id=int(artifact.id),
        message="TRAIN X contains no rows marked as TEST",
        rows_total=row_count,
        details={"role_columns": role_columns},
    )


def _check_absolute_paths_absent(
    artifact_id: int,
    paths: list[Path],
    schema: pa.Schema,
    row_count: int,
) -> QualityCheckRecord:
    string_columns = [
        field.name
        for field in schema
        if pa.types.is_string(field.type) or pa.types.is_large_string(field.type)
    ]
    if not string_columns:
        return pass_check(
            check_group="leakage",
            check_name="local_absolute_paths_absent",
            artifact_type="model_ready",
            artifact_id=artifact_id,
            message="X has no string columns where local paths could appear",
            rows_total=row_count,
        )
    path_counts: dict[str, int] = {}
    for column in string_columns:
        expression = (
            f"SUM(CASE WHEN regexp_matches(CAST({quoted_identifier(column)} AS VARCHAR), "
            r"'^[A-Za-z]:[\\/]|^/[^/].*') THEN 1 ELSE 0 END)"
        )
        count = int(duckdb_scalar(paths, expression))
        if count:
            path_counts[column] = count
    if path_counts:
        total = sum(path_counts.values())
        return fail_check(
            check_group="leakage",
            check_name="local_absolute_paths_absent",
            artifact_type="model_ready",
            artifact_id=artifact_id,
            message="model-ready X contains local absolute path values",
            rows_total=row_count,
            rows_failed=total,
            leakage_issue_count=total,
            details={"path_value_counts": path_counts},
        )
    return pass_check(
        check_group="leakage",
        check_name="local_absolute_paths_absent",
        artifact_type="model_ready",
        artifact_id=artifact_id,
        message="model-ready X contains no local absolute path values",
        rows_total=row_count,
        details={"string_columns_checked": string_columns},
    )


def _check_test_usage_metadata_absent(
    artifact: ModelReadyArtifact,
    artifact_id: int,
) -> QualityCheckRecord:
    metadata = artifact.metadata_json or {}
    suspicious_keys = sorted(
        key
        for key in metadata
        if "test" in str(key).lower()
        and any(token in str(key).lower() for token in ("selection", "threshold", "tuning", "fit"))
    )
    suspicious_values = sorted(
        key
        for key, value in metadata.items()
        if isinstance(value, str)
        and "test" in value.lower()
        and any(token in value.lower() for token in ("selection", "threshold", "tuning", "fit"))
    )
    if suspicious_keys or suspicious_values:
        return fail_check(
            check_group="leakage",
            check_name="feature_selection_threshold_tuning_not_using_test",
            artifact_type="model_ready",
            artifact_id=artifact_id,
            message="model-ready metadata suggests feature selection or threshold tuning used TEST",
            leakage_issue_count=len(suspicious_keys) + len(suspicious_values),
            details={"suspicious_keys": suspicious_keys, "suspicious_values": suspicious_values},
        )
    return pass_check(
        check_group="leakage",
        check_name="feature_selection_threshold_tuning_not_using_test",
        artifact_type="model_ready",
        artifact_id=artifact_id,
        message="model-ready metadata does not indicate TEST-based selection or threshold tuning",
    )


def _check_validation_test_balancing_absent(
    artifact: ModelReadyArtifact,
    artifact_id: int,
) -> QualityCheckRecord:
    metadata = artifact.metadata_json or {}
    balancing = metadata.get("balancing") or metadata.get("balancing_method")
    if artifact.role in {"VALIDATION", "TEST"} and balancing not in {None, "", "none", "report_only", "class_weight_metadata"}:
        return fail_check(
            check_group="leakage",
            check_name="balancing_only_train",
            artifact_type="model_ready",
            artifact_id=artifact_id,
            message="balancing metadata is present on VALIDATION/TEST artifact",
            leakage_issue_count=1,
            details={"role": artifact.role, "balancing": balancing},
        )
    return pass_check(
        check_group="leakage",
        check_name="balancing_only_train",
        artifact_type="model_ready",
        artifact_id=artifact_id,
        message="balancing metadata is absent from non-TRAIN artifact or allowed as report-only metadata",
        details={"role": artifact.role, "balancing": balancing},
    )


def _check_preprocessing_fit_role(artifacts: list[PreprocessingArtifact]) -> list[QualityCheckRecord]:
    bad = [artifact for artifact in artifacts if artifact.fitted_on_role != "TRAIN"]
    if bad:
        return [
            fail_check(
                check_group="leakage",
                check_name="preprocessing_fitted_only_on_train",
                artifact_type="preprocessing",
                message="preprocessing artifacts were fitted on non-TRAIN roles",
                leakage_issue_count=len(bad),
                details={"artifact_ids": [int(artifact.id) for artifact in bad]},
            )
        ]
    return [
        pass_check(
            check_group="leakage",
            check_name="preprocessing_fitted_only_on_train",
            artifact_type="preprocessing",
            message="all preprocessing artifacts are fitted on TRAIN",
            rows_total=len(artifacts),
        )
    ]


def _list_model_ready_artifacts(
    session: Session,
    *,
    experiment_id: str,
    branch: str | None,
    role: str | None,
    feature_group: str | None,
) -> list[ModelReadyArtifact]:
    statement = (
        select(ModelReadyArtifact)
        .where(
            ModelReadyArtifact.metadata_json["experiment_id"].as_string() == experiment_id,
            ModelReadyArtifact.status.in_(("SUCCESS", "PARTIAL_SUCCESS", "BLOCKED", "BLOCKED_BY_LEAKAGE", "BLOCKED_BY_QUALITY")),
        )
        .order_by(ModelReadyArtifact.role.asc(), ModelReadyArtifact.data_type.asc(), ModelReadyArtifact.id.asc())
    )
    if branch is not None:
        statement = statement.where(ModelReadyArtifact.branch == branch)
    if role is not None:
        statement = statement.where(ModelReadyArtifact.role == role)
    if feature_group is not None:
        statement = statement.join(FeatureArtifact, ModelReadyArtifact.feature_artifact_id == FeatureArtifact.id).where(
            FeatureArtifact.feature_group == feature_group
        )
    return list(session.execute(statement).scalars())


def _list_preprocessing_artifacts(
    session: Session,
    *,
    branch: str | None,
    feature_group: str | None,
) -> list[PreprocessingArtifact]:
    statement = select(PreprocessingArtifact).order_by(PreprocessingArtifact.id.asc())
    if branch is not None:
        statement = statement.where(PreprocessingArtifact.branch == branch)
    if feature_group is not None:
        statement = statement.where(PreprocessingArtifact.feature_group == feature_group)
    return list(session.execute(statement).scalars())
