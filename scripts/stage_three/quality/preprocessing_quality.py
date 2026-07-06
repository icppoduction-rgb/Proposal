"""Preprocessing artifact quality checks for Stage Three."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scripts.stage_three.quality.common import (
    QualityCheckRecord,
    fail_check,
    parquet_paths_from_catalog_path,
    pass_check,
    resolve_artifact_path,
)


def run_preprocessing_quality_checks(
    preprocessing_artifacts: list[Any],
    *,
    storage_root: str | Path,
) -> list[QualityCheckRecord]:
    """Validate registered preprocessing artifacts."""
    records: list[QualityCheckRecord] = []
    for artifact in preprocessing_artifacts:
        artifact_id = int(artifact.id)
        records.append(_check_preprocessing_exists(artifact, artifact_id, storage_root=storage_root))
        records.append(_check_fitted_on_train(artifact, artifact_id))
    return records


def _check_preprocessing_exists(
    artifact: Any,
    artifact_id: int,
    *,
    storage_root: str | Path,
) -> QualityCheckRecord:
    path = resolve_artifact_path(getattr(artifact, "artifact_path"), storage_root=storage_root)
    if not path.exists():
        return fail_check(
            check_group="preprocessing_quality",
            check_name="preprocessing_artifact_exists",
            artifact_type="preprocessing",
            artifact_id=artifact_id,
            message="preprocessing artifact path does not exist",
            details={"artifact_path": path.as_posix()},
        )
    if path.is_file() and path.suffix.lower() == ".parquet":
        rows = pq.read_metadata(path).num_rows
        if rows <= 0:
            return fail_check(
                check_group="preprocessing_quality",
                check_name="preprocessing_artifact_exists",
                artifact_type="preprocessing",
                artifact_id=artifact_id,
                message="preprocessing artifact Parquet file is empty",
                rows_total=rows,
                details={"artifact_path": path.as_posix()},
            )
    return pass_check(
        check_group="preprocessing_quality",
        check_name="preprocessing_artifact_exists",
        artifact_type="preprocessing",
        artifact_id=artifact_id,
        message="preprocessing artifact exists",
        details={"artifact_path": path.as_posix()},
    )


def _check_fitted_on_train(artifact: Any, artifact_id: int) -> QualityCheckRecord:
    fitted_on_role = getattr(artifact, "fitted_on_role", None)
    if fitted_on_role != "TRAIN":
        return fail_check(
            check_group="preprocessing_quality",
            check_name="fitted_on_role_train",
            artifact_type="preprocessing",
            artifact_id=artifact_id,
            message="preprocessing artifact was not fitted on TRAIN",
            details={"fitted_on_role": fitted_on_role},
        )
    return pass_check(
        check_group="preprocessing_quality",
        check_name="fitted_on_role_train",
        artifact_type="preprocessing",
        artifact_id=artifact_id,
        message="preprocessing artifact fitted_on_role is TRAIN",
        details={"fitted_on_role": fitted_on_role},
    )


def check_model_ready_preprocessing_metadata(
    preprocessing_metadata_artifacts: list[Any],
    *,
    storage_root: str | Path,
) -> list[QualityCheckRecord]:
    """Validate model-ready preprocessing metadata artifacts."""
    records: list[QualityCheckRecord] = []
    if not preprocessing_metadata_artifacts:
        return [
            fail_check(
                check_group="model_ready_quality",
                check_name="preprocessing_artifact_exists",
                artifact_type="model_ready",
                message="model-ready preprocessing_metadata artifact is missing",
            )
        ]
    for artifact in preprocessing_metadata_artifacts:
        artifact_id = int(artifact.id)
        paths = parquet_paths_from_catalog_path(getattr(artifact, "artifact_path"), storage_root=storage_root)
        metadata = getattr(artifact, "metadata_json", None) or {}
        if not paths:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="preprocessing_artifact_exists",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="preprocessing_metadata artifact path does not exist",
                    details={"artifact_path": getattr(artifact, "artifact_path", None)},
                )
            )
            continue
        row_count = sum(pq.read_metadata(path).num_rows for path in paths)
        if row_count <= 0:
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="preprocessing_artifact_exists",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="preprocessing_metadata artifact is empty",
                    rows_total=row_count,
                )
            )
        else:
            records.append(
                pass_check(
                    check_group="model_ready_quality",
                    check_name="preprocessing_artifact_exists",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="preprocessing_metadata artifact exists",
                    rows_total=row_count,
                )
            )
        fitted_on_role = metadata.get("fitted_on_role")
        if fitted_on_role != "TRAIN":
            records.append(
                fail_check(
                    check_group="model_ready_quality",
                    check_name="fitted_on_role_train",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="preprocessing metadata does not declare fitted_on_role=TRAIN",
                    details={"fitted_on_role": fitted_on_role},
                )
            )
        else:
            records.append(
                pass_check(
                    check_group="model_ready_quality",
                    check_name="fitted_on_role_train",
                    artifact_type="model_ready",
                    artifact_id=artifact_id,
                    message="preprocessing metadata declares fitted_on_role=TRAIN",
                    details={"fitted_on_role": fitted_on_role},
                )
            )
    return records
