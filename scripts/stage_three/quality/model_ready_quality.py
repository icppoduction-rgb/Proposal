"""Model-ready artifact quality checks for Stage Three."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts.stage_three.quality.common import (
    QualityCheckRecord,
    duckdb_dict,
    fail_check,
    parquet_paths_from_catalog_path,
    parquet_row_count,
    parquet_schema,
    pass_check,
    quoted_identifier,
    warn_check,
)
from scripts.stage_three.quality.preprocessing_quality import check_model_ready_preprocessing_metadata
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths
from scripts.stage_three.quality.class_balance_report import TASK15_REPORT_FILENAME
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS


SUPERVISED_TARGET_DEFAULT = "label_binary"


def run_model_ready_quality_checks(
    model_ready_artifacts: list[Any],
    *,
    storage_root: str | Path,
    target: str = SUPERVISED_TARGET_DEFAULT,
) -> list[QualityCheckRecord]:
    """Run quality checks for model-ready artifacts."""
    by_role_type = _index_by_role_type(model_ready_artifacts)
    roles = sorted(role for role in by_role_type if role != "EXPERIMENTS")
    records: list[QualityCheckRecord] = []
    x_schema_by_role: dict[str, list[str]] = {}
    for role in roles:
        records.extend(_check_role_x(role, by_role_type, storage_root=storage_root, x_schema_by_role=x_schema_by_role))
        records.extend(_check_role_y(role, by_role_type, storage_root=storage_root, target=target))
        records.append(_check_x_y_row_counts(role, by_role_type, storage_root=storage_root))
        records.extend(_check_role_metadata_traceability(role, by_role_type, storage_root=storage_root))
    records.append(_check_x_schema_consistency(x_schema_by_role))
    records.extend(
        check_model_ready_preprocessing_metadata(
            by_role_type.get("EXPERIMENTS", {}).get("preprocessing_metadata", []),
            storage_root=storage_root,
        )
    )
    records.append(_check_class_balance_report())
    return records


def _check_role_x(
    role: str,
    by_role_type: dict[str, dict[str, list[Any]]],
    *,
    storage_root: str | Path,
    x_schema_by_role: dict[str, list[str]],
) -> list[QualityCheckRecord]:
    artifacts = by_role_type[role].get("X", [])
    if not artifacts:
        return [
            fail_check(
                check_group="model_ready_quality",
                check_name="X_exists_not_empty",
                artifact_type="model_ready",
                message=f"X artifact is missing for role={role}",
                details={"role": role},
            )
        ]
    records: list[QualityCheckRecord] = []
    for artifact in artifacts:
        artifact_id = int(artifact.id)
        paths = parquet_paths_from_catalog_path(getattr(artifact, "artifact_path"), storage_root=storage_root)
        if not paths:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="X_exists_not_empty",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="X artifact path does not exist",
                    details={"role": role, "artifact_path": getattr(artifact, "artifact_path", None)},
                )
            )
            continue
        row_count = parquet_row_count(paths)
        schema = parquet_schema(paths)
        x_schema_by_role[role] = list(schema.names)
        if row_count <= 0:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="X_exists_not_empty",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="X artifact is empty",
                    rows_total=row_count,
                    details={"role": role},
                )
            )
        else:
            records.append(
                pass_check(
                    check_group="model_ready_quality",
                    check_name="X_exists_not_empty",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="X artifact exists and is not empty",
                    rows_total=row_count,
                    details={"role": role, "columns": list(schema.names)},
                )
            )
        records.append(_check_x_forbidden_columns(artifact_id, role, list(schema.names)))
    return records


def _check_role_y(
    role: str,
    by_role_type: dict[str, dict[str, list[Any]]],
    *,
    storage_root: str | Path,
    target: str,
) -> list[QualityCheckRecord]:
    artifacts = by_role_type[role].get("y", [])
    if not artifacts:
        return [
            fail_check(
                check_group="model_ready_quality",
                check_name="y_exists_for_supervised_pipeline",
                artifact_type="model_ready",
                message=f"y artifact is missing for supervised role={role}",
                details={"role": role, "target": target},
            )
        ]
    records: list[QualityCheckRecord] = []
    for artifact in artifacts:
        artifact_id = int(artifact.id)
        paths = parquet_paths_from_catalog_path(getattr(artifact, "artifact_path"), storage_root=storage_root)
        if not paths:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="y_exists_for_supervised_pipeline",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="y artifact path does not exist",
                    details={"role": role, "artifact_path": getattr(artifact, "artifact_path", None)},
                )
            )
            continue
        row_count = parquet_row_count(paths)
        columns = list(parquet_schema(paths).names)
        if target not in columns:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="y_exists_for_supervised_pipeline",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="y artifact is missing the supervised target column",
                    rows_total=row_count,
                    details={"role": role, "target": target, "columns": columns},
                )
            )
            continue
        distribution = duckdb_dict(
            paths,
            f"SELECT CAST({quoted_identifier(target)} AS VARCHAR), COUNT(*) FROM {{relation}} GROUP BY 1 ORDER BY 1",
        )
        records.append(
            pass_check(
                check_group="model_ready_quality",
                check_name="y_exists_for_supervised_pipeline",
                artifact_type="model_ready",
                artifact_id=artifact_id,
                message="y artifact exists for supervised pipeline",
                rows_total=row_count,
                details={"role": role, "target": target, "distribution": distribution},
            )
        )
    return records


def _check_x_y_row_counts(
    role: str,
    by_role_type: dict[str, dict[str, list[Any]]],
    *,
    storage_root: str | Path,
) -> QualityCheckRecord:
    x_artifact = _first(by_role_type[role].get("X", []))
    y_artifact = _first(by_role_type[role].get("y", []))
    if x_artifact is None or y_artifact is None:
        return fail_check(
            check_group="model_ready_quality",
            check_name="X_y_row_counts_match",
            artifact_type="model_ready",
            message=f"cannot compare X/y row counts for role={role}; one artifact is missing",
            details={"role": role},
        )
    x_rows = _safe_row_count(x_artifact, storage_root=storage_root)
    y_rows = _safe_row_count(y_artifact, storage_root=storage_root)
    if x_rows != y_rows:
        return fail_check(
            check_group="model_ready_quality",
            check_name="X_y_row_counts_match",
            artifact_type="model_ready",
            artifact_id=int(x_artifact.id),
            message="X/y row counts do not match",
            rows_total=x_rows,
            rows_failed=abs(x_rows - y_rows),
            details={"role": role, "x_rows": x_rows, "y_rows": y_rows, "y_artifact_id": int(y_artifact.id)},
        )
    return pass_check(
        check_group="model_ready_quality",
        check_name="X_y_row_counts_match",
        artifact_type="model_ready",
        artifact_id=int(x_artifact.id),
        message="X/y row counts match",
        rows_total=x_rows,
        details={"role": role, "x_rows": x_rows, "y_rows": y_rows, "y_artifact_id": int(y_artifact.id)},
    )


def _check_x_schema_consistency(x_schema_by_role: dict[str, list[str]]) -> QualityCheckRecord:
    if not x_schema_by_role:
        return fail_check(
            check_group="model_ready_quality",
            check_name="X_schemas_match_between_splits",
            artifact_type="model_ready",
            message="no X schemas were available for comparison",
        )
    first_role, first_schema = next(iter(sorted(x_schema_by_role.items())))
    mismatches = {
        role: schema
        for role, schema in x_schema_by_role.items()
        if schema != first_schema
    }
    if mismatches:
        return fail_check(
            check_group="model_ready_quality",
            check_name="X_schemas_match_between_splits",
            artifact_type="model_ready",
            message="X schemas differ between TRAIN/VALIDATION/TEST",
            schema_mismatch_count=len(mismatches),
            details={"reference_role": first_role, "reference_schema": first_schema, "mismatches": mismatches},
        )
    return pass_check(
        check_group="model_ready_quality",
        check_name="X_schemas_match_between_splits",
        artifact_type="model_ready",
        message="X schemas match between available splits",
        details={"x_schema_by_role": x_schema_by_role},
    )


def _check_role_metadata_traceability(
    role: str,
    by_role_type: dict[str, dict[str, list[Any]]],
    *,
    storage_root: str | Path,
) -> list[QualityCheckRecord]:
    records: list[QualityCheckRecord] = []
    for data_type in ("metadata", "traceability"):
        artifacts = by_role_type[role].get(data_type, [])
        if not artifacts:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="metadata_traceability_artifacts_exist",
                    artifact_type="model_ready",
                    message=f"{data_type} artifact is missing for role={role}",
                    details={"role": role, "data_type": data_type},
                )
            )
            continue
        artifact = artifacts[0]
        artifact_id = int(artifact.id)
        paths = parquet_paths_from_catalog_path(getattr(artifact, "artifact_path"), storage_root=storage_root)
        row_count = parquet_row_count(paths) if paths else 0
        if not paths or row_count <= 0:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="metadata_traceability_artifacts_exist",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message=f"{data_type} artifact path is missing or empty",
                    rows_total=row_count,
                    details={"role": role, "data_type": data_type},
                )
            )
        else:
            records.append(
                pass_check(
                    check_group="model_ready_quality",
                    check_name="metadata_traceability_artifacts_exist",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message=f"{data_type} artifact exists",
                    rows_total=row_count,
                    details={"role": role, "data_type": data_type},
                )
            )
    return records


def _check_x_forbidden_columns(artifact_id: int, role: str, columns: list[str]) -> QualityCheckRecord:
    forbidden = sorted(
        column
        for column in columns
        if column in FORBIDDEN_X_COLUMNS or column.startswith("label_")
    )
    if forbidden:
        return fail_check(
            check_group="model_ready_quality",
            check_name="X_feature_columns_do_not_contain_forbidden_fields",
            artifact_type="model_ready",
            artifact_id=artifact_id,
            message="model-ready X contains forbidden leakage/source/label columns",
            leakage_issue_count=len(forbidden),
            details={"role": role, "forbidden_columns": forbidden},
        )
    return pass_check(
        check_group="model_ready_quality",
        check_name="X_feature_columns_do_not_contain_forbidden_fields",
        artifact_type="model_ready",
        artifact_id=artifact_id,
        message="model-ready X has no forbidden columns",
        details={"role": role},
    )


def _check_class_balance_report() -> QualityCheckRecord:
    try:
        paths = build_stage_three_task_report_paths(TASK15_REPORT_FILENAME)
    except RuntimeError as exc:
        return warn_check(
            check_group="model_ready_quality",
            check_name="class_balance_report_exists",
            artifact_type="model_ready",
            message="class balance report path cannot be resolved",
            details={"error": str(exc)},
        )
    exists = paths.ru.exists() or paths.en.exists()
    if not exists:
        return warn_check(
            check_group="model_ready_quality",
            check_name="class_balance_report_exists",
            artifact_type="model_ready",
            message="class balance report was not found; y distributions were still checked",
            details={"ru": str(paths.ru), "en": str(paths.en)},
        )
    return pass_check(
        check_group="model_ready_quality",
        check_name="class_balance_report_exists",
        artifact_type="model_ready",
        message="class balance report exists",
        details={"ru": str(paths.ru), "en": str(paths.en)},
    )


def _index_by_role_type(model_ready_artifacts: list[Any]) -> dict[str, dict[str, list[Any]]]:
    indexed: dict[str, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
    for artifact in model_ready_artifacts:
        indexed[getattr(artifact, "role")][getattr(artifact, "data_type")].append(artifact)
    return {role: dict(values) for role, values in indexed.items()}


def _safe_row_count(artifact: Any, *, storage_root: str | Path) -> int:
    paths = parquet_paths_from_catalog_path(getattr(artifact, "artifact_path"), storage_root=storage_root)
    return parquet_row_count(paths) if paths else 0


def _first(values: list[Any]) -> Any | None:
    return values[0] if values else None
