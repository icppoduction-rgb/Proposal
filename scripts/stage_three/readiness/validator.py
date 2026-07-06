"""Validate Stage Two normalized outputs before Stage Three processing."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from config import (
    FEATURE_ARTIFACT_SCHEMA_PATH,
    MODEL_READY_SCHEMA_PATH,
    PATH_DATA_STORAGE,
)
from scripts.db.models import Dataset, DatasetFile, NormalizedArtifact, ParserRun
from scripts.stage_three.requests import ValidateInputsRequest


PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

ALLOWED_PARSER_STATUSES = frozenset({"SUCCESS", "PARTIAL_SUCCESS"})
ALLOWED_ARTIFACT_STATUSES = frozenset({"SUCCESS", "PARTIAL_SUCCESS"})
ALLOWED_DATASET_FILE_STATUSES = frozenset({"PARSED", "PARTIALLY_PARSED"})

DRY_RUN_SOURCE_GROUPS = frozenset({"STAGE_TWO_E2E_DRY_RUN"})
BLOCKING_PARSER_STATUSES = frozenset({"RUNNING", "FAILED", "SKIPPED"})
BLOCKING_ARTIFACT_STATUSES = frozenset({"PENDING", "RUNNING", "FAILED", "SKIPPED", "BLOCKED"})
BLOCKING_DATASET_FILE_STATUSES = frozenset(
    {
        "DISCOVERED",
        "REGISTERED",
        "CHANGED",
        "EMPTY_FILE",
        "UNSUPPORTED_FORMAT",
        "READY_FOR_PARSING",
        "FAILED",
        "SKIPPED",
    }
)

REQUIRED_TRACEABILITY_COLUMNS = frozenset(
    {
        "event_uid",
        "dataset_id",
        "file_id",
        "dataset_name",
        "dataset_role",
        "branch",
        "source_format",
        "source_file_path",
        "parser_name",
        "parser_version",
        "parser_run_id",
        "schema_name",
        "schema_version",
    }
)
REQUIRED_LABEL_COLUMNS = frozenset({"label_binary", "label_source", "label_status"})
LABEL_SAMPLE_ROWS = 256


@dataclass(frozen=True)
class ReadinessCheck:
    """One readiness gate check result."""

    name: str
    status: str
    blocking: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedArtifactSummary:
    """Lightweight normalized artifact metadata used in reports."""

    artifact_id: int
    parser_run_id: int
    dataset_file_id: int
    dataset_id: int
    branch: str
    role: str
    source_format: str
    normalized_path: str
    status: str
    row_count: int | None
    parquet_rows: int | None = None
    parquet_columns: int | None = None


@dataclass(frozen=True)
class StageThreeReadinessResult:
    """Serializable readiness gate result."""

    status: str
    branch: str
    role: str
    checked_branches_roles: list[dict[str, str]]
    normalized_artifact_count: int
    normalized_artifacts_by_status: dict[str, int]
    parser_runs_by_status: dict[str, int]
    dataset_files_by_status: dict[str, int]
    checks: list[ReadinessCheck]
    blocking_issues: list[str]
    next_actions: list[str]
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly payload."""
        return asdict(self)


def validate_stage_three_inputs(
    request: ValidateInputsRequest,
    session: Session,
    *,
    storage_root: str | Path | None = None,
    feature_schema_path: str | Path = FEATURE_ARTIFACT_SCHEMA_PATH,
    model_ready_schema_path: str | Path = MODEL_READY_SCHEMA_PATH,
) -> StageThreeReadinessResult:
    """Run the Stage Three input readiness gate for one branch/role."""
    root = _resolve_storage_root(storage_root)
    rows = _fetch_normalized_rows(session, branch=request.branch, role=request.role)
    checks: list[ReadinessCheck] = []

    checks.append(_check_required_schema_files(feature_schema_path, model_ready_schema_path))
    checks.append(_check_normalized_artifacts_exist(rows, request))
    checks.append(_check_parser_run_statuses(rows))
    checks.append(_check_dataset_file_statuses(rows))
    checks.append(_check_dataset_links(rows, request))
    checks.append(_check_normalized_artifact_statuses(rows))

    parquet_check, parquet_summaries = _check_parquet_files(rows, root)
    checks.append(parquet_check)
    checks.append(_check_traceability_columns(parquet_summaries))
    checks.append(_check_label_columns(parquet_summaries))
    checks.append(_check_test_fit_policy(rows, request))

    status = _overall_status(checks)
    blocking_issues = [check.message for check in checks if check.status == FAIL and check.blocking]
    return StageThreeReadinessResult(
        status=status,
        branch=request.branch,
        role=request.role,
        checked_branches_roles=[{"branch": request.branch, "role": request.role}],
        normalized_artifact_count=len(rows),
        normalized_artifacts_by_status=_count_statuses(row.artifact.status for row in rows),
        parser_runs_by_status=_count_statuses(row.parser_run.status for row in rows),
        dataset_files_by_status=_count_statuses(row.dataset_file.status for row in rows),
        checks=checks,
        blocking_issues=blocking_issues,
        next_actions=_next_actions(status, request, blocking_issues),
    )


@dataclass(frozen=True)
class _ArtifactRow:
    artifact: NormalizedArtifact
    parser_run: ParserRun
    dataset_file: DatasetFile
    dataset: Dataset


@dataclass(frozen=True)
class _ParquetSummary:
    artifact: NormalizedArtifactSummary
    path: str
    exists: bool
    readable: bool
    row_count: int | None
    columns: set[str]
    missing_traceability_columns: list[str]
    missing_label_columns: list[str]
    label_status_values: dict[str, int]
    label_source_values: dict[str, int]
    error: str | None = None


def _fetch_normalized_rows(session: Session, *, branch: str, role: str) -> list[_ArtifactRow]:
    statement = (
        select(NormalizedArtifact, ParserRun, DatasetFile, Dataset)
        .join(ParserRun, NormalizedArtifact.parser_run_id == ParserRun.id)
        .join(DatasetFile, NormalizedArtifact.file_id == DatasetFile.id)
        .join(Dataset, NormalizedArtifact.dataset_id == Dataset.id)
        .where(
            NormalizedArtifact.branch == branch,
            NormalizedArtifact.role == role,
            Dataset.is_active.is_(True),
            or_(Dataset.source_group.is_(None), Dataset.source_group.notin_(DRY_RUN_SOURCE_GROUPS)),
        )
        .order_by(NormalizedArtifact.id.asc())
    )
    return [
        _ArtifactRow(
            artifact=artifact,
            parser_run=parser_run,
            dataset_file=dataset_file,
            dataset=dataset,
        )
        for artifact, parser_run, dataset_file, dataset in session.execute(statement).all()
    ]


def _check_required_schema_files(
    feature_schema_path: str | Path,
    model_ready_schema_path: str | Path,
) -> ReadinessCheck:
    required = {
        "schemas/features/feature_artifact_v1.json": Path(feature_schema_path),
        "schemas/model_ready/model_ready_v1.json": Path(model_ready_schema_path),
    }
    missing = [name for name, path in required.items() if not path.exists()]
    return ReadinessCheck(
        name="required_schema_files",
        status=PASS if not missing else FAIL,
        blocking=bool(missing),
        message="Required Stage Three schema files are present."
        if not missing
        else "Required Stage Three schema files are missing.",
        details={
            "required": {name: str(path) for name, path in required.items()},
            "missing": missing,
        },
    )


def _check_normalized_artifacts_exist(
    rows: list[_ArtifactRow],
    request: ValidateInputsRequest,
) -> ReadinessCheck:
    return ReadinessCheck(
        name="normalized_artifacts_exist",
        status=PASS if rows else FAIL,
        blocking=not rows,
        message=f"Found {len(rows)} normalized artifacts for {request.branch}/{request.role}."
        if rows
        else f"No normalized artifacts found for {request.branch}/{request.role}.",
        details={"count": len(rows), "branch": request.branch, "role": request.role},
    )


def _check_parser_run_statuses(rows: list[_ArtifactRow]) -> ReadinessCheck:
    counts = _count_statuses(row.parser_run.status for row in rows)
    blocking = _statuses_present(counts, BLOCKING_PARSER_STATUSES)
    partial_count = counts.get("PARTIAL_SUCCESS", 0)
    status = FAIL if blocking else (WARN if partial_count else PASS)
    message = "Parser runs are successful."
    if blocking:
        message = "Some parser_runs are not complete enough for Stage Three."
    elif partial_count:
        message = "Parser runs include allowed PARTIAL_SUCCESS rows."
    return ReadinessCheck(
        name="parser_run_statuses",
        status=status,
        blocking=blocking,
        message=message,
        details={
            "allowed_statuses": sorted(ALLOWED_PARSER_STATUSES),
            "counts": counts,
        },
    )


def _check_dataset_file_statuses(rows: list[_ArtifactRow]) -> ReadinessCheck:
    counts = _count_statuses(row.dataset_file.status for row in rows)
    blocking = _statuses_present(counts, BLOCKING_DATASET_FILE_STATUSES)
    partial_count = counts.get("PARTIALLY_PARSED", 0)
    status = FAIL if blocking else (WARN if partial_count else PASS)
    message = "dataset_files statuses are compatible with feature extraction."
    if blocking:
        message = "Some dataset_files statuses are incompatible with downstream feature extraction."
    elif partial_count:
        message = "dataset_files include PARTIALLY_PARSED rows; downstream can proceed with warnings."
    return ReadinessCheck(
        name="dataset_file_statuses",
        status=status,
        blocking=blocking,
        message=message,
        details={
            "allowed_statuses": sorted(ALLOWED_DATASET_FILE_STATUSES),
            "counts": counts,
        },
    )


def _check_dataset_links(rows: list[_ArtifactRow], request: ValidateInputsRequest) -> ReadinessCheck:
    mismatches = []
    inactive = []
    for row in rows:
        dataset = row.dataset
        dataset_file = row.dataset_file
        if dataset.branch != request.branch or dataset.role != request.role:
            mismatches.append({"dataset_id": dataset.id, "branch": dataset.branch, "role": dataset.role})
        if dataset_file.branch != request.branch or dataset_file.role != request.role:
            mismatches.append(
                {
                    "dataset_file_id": dataset_file.id,
                    "branch": dataset_file.branch,
                    "role": dataset_file.role,
                }
            )
        if not dataset.is_active:
            inactive.append({"dataset_id": dataset.id, "name": dataset.name})
    blocking = bool(mismatches)
    status = FAIL if blocking else (WARN if inactive else PASS)
    message = "datasets and dataset_files match the requested branch/role."
    if blocking:
        message = "Catalog branch/role links do not match the requested Stage Three input."
    elif inactive:
        message = "Some linked datasets are inactive."
    return ReadinessCheck(
        name="datasets_and_files_links",
        status=status,
        blocking=blocking,
        message=message,
        details={"mismatches": mismatches, "inactive_datasets": inactive},
    )


def _check_normalized_artifact_statuses(rows: list[_ArtifactRow]) -> ReadinessCheck:
    counts = _count_statuses(row.artifact.status for row in rows)
    blocking = _statuses_present(counts, BLOCKING_ARTIFACT_STATUSES)
    partial_count = counts.get("PARTIAL_SUCCESS", 0)
    status = FAIL if blocking else (WARN if partial_count else PASS)
    message = "normalized_artifacts statuses are successful."
    if blocking:
        message = "Some normalized_artifacts are blocked, failed, skipped, pending, or running."
    elif partial_count:
        message = "normalized_artifacts include allowed PARTIAL_SUCCESS rows."
    return ReadinessCheck(
        name="normalized_artifact_statuses",
        status=status,
        blocking=blocking,
        message=message,
        details={
            "allowed_statuses": sorted(ALLOWED_ARTIFACT_STATUSES),
            "counts": counts,
        },
    )


def _check_parquet_files(
    rows: list[_ArtifactRow],
    storage_root: Path,
) -> tuple[ReadinessCheck, list[_ParquetSummary]]:
    summaries = [_inspect_parquet(row, storage_root) for row in rows]
    missing = [summary.path for summary in summaries if not summary.exists]
    unreadable = [
        {"path": summary.path, "error": summary.error}
        for summary in summaries
        if summary.exists and not summary.readable
    ]
    empty = [
        summary.path
        for summary in summaries
        if summary.readable and (summary.row_count is None or summary.row_count <= 0)
    ]
    row_count_mismatches = [
        {
            "artifact_id": summary.artifact.artifact_id,
            "catalog_row_count": summary.artifact.row_count,
            "parquet_rows": summary.row_count,
        }
        for summary in summaries
        if summary.readable
        and summary.artifact.row_count is not None
        and summary.row_count is not None
        and summary.artifact.row_count != summary.row_count
    ]
    blocking = bool(missing or unreadable or empty)
    status = FAIL if blocking else (WARN if row_count_mismatches else PASS)
    message = "Normalized Parquet files exist and are readable through metadata/schema reads."
    if blocking:
        message = "Some normalized Parquet files are missing, unreadable, or empty."
    elif row_count_mismatches:
        message = "Normalized Parquet files are readable, but catalog row counts differ."
    return (
        ReadinessCheck(
            name="normalized_parquet_readability",
            status=status,
            blocking=blocking,
            message=message,
            details={
                "checked_files": len(summaries),
                "missing_files": missing,
                "unreadable_files": unreadable,
                "empty_files": empty,
                "row_count_mismatches": row_count_mismatches,
            },
        ),
        summaries,
    )


def _inspect_parquet(row: _ArtifactRow, storage_root: Path) -> _ParquetSummary:
    artifact = row.artifact
    path = _resolve_artifact_path(storage_root, artifact.normalized_path)
    base = NormalizedArtifactSummary(
        artifact_id=artifact.id,
        parser_run_id=artifact.parser_run_id,
        dataset_file_id=artifact.file_id,
        dataset_id=artifact.dataset_id,
        branch=artifact.branch,
        role=artifact.role,
        source_format=artifact.source_format,
        normalized_path=artifact.normalized_path,
        status=artifact.status,
        row_count=artifact.row_count,
    )
    if not path.exists():
        return _ParquetSummary(
            artifact=base,
            path=str(path),
            exists=False,
            readable=False,
            row_count=None,
            columns=set(),
            missing_traceability_columns=sorted(REQUIRED_TRACEABILITY_COLUMNS),
            missing_label_columns=sorted(REQUIRED_LABEL_COLUMNS),
            label_status_values={},
            label_source_values={},
            error="file does not exist",
        )
    try:
        metadata = pq.read_metadata(path)
        schema = pq.read_schema(path)
        columns = set(schema.names)
        label_status_values, label_source_values = _sample_label_values(path, columns)
        row_count = int(metadata.num_rows)
        enriched_base = NormalizedArtifactSummary(
            artifact_id=base.artifact_id,
            parser_run_id=base.parser_run_id,
            dataset_file_id=base.dataset_file_id,
            dataset_id=base.dataset_id,
            branch=base.branch,
            role=base.role,
            source_format=base.source_format,
            normalized_path=base.normalized_path,
            status=base.status,
            row_count=base.row_count,
            parquet_rows=row_count,
            parquet_columns=len(columns),
        )
        return _ParquetSummary(
            artifact=enriched_base,
            path=str(path),
            exists=True,
            readable=True,
            row_count=row_count,
            columns=columns,
            missing_traceability_columns=sorted(REQUIRED_TRACEABILITY_COLUMNS.difference(columns)),
            missing_label_columns=sorted(REQUIRED_LABEL_COLUMNS.difference(columns)),
            label_status_values=label_status_values,
            label_source_values=label_source_values,
        )
    except Exception as exc:
        return _ParquetSummary(
            artifact=base,
            path=str(path),
            exists=True,
            readable=False,
            row_count=None,
            columns=set(),
            missing_traceability_columns=sorted(REQUIRED_TRACEABILITY_COLUMNS),
            missing_label_columns=sorted(REQUIRED_LABEL_COLUMNS),
            label_status_values={},
            label_source_values={},
            error=str(exc),
        )


def _sample_label_values(path: Path, columns: set[str]) -> tuple[dict[str, int], dict[str, int]]:
    projected = [column for column in ("label_status", "label_source") if column in columns]
    if not projected:
        return {}, {}
    parquet_file = pq.ParquetFile(path)
    if parquet_file.num_row_groups == 0:
        return {}, {}
    table = parquet_file.read_row_group(0, columns=projected, use_threads=False).slice(0, LABEL_SAMPLE_ROWS)
    values: dict[str, dict[str, int]] = {}
    for column in projected:
        counter: Counter[str] = Counter()
        for item in table.column(column).to_pylist():
            key = "<NULL>" if item is None else str(item)
            counter[key] += 1
        values[column] = dict(sorted(counter.items()))
    return values.get("label_status", {}), values.get("label_source", {})


def _check_traceability_columns(summaries: list[_ParquetSummary]) -> ReadinessCheck:
    missing_by_file = [
        {
            "artifact_id": summary.artifact.artifact_id,
            "path": summary.path,
            "missing_columns": summary.missing_traceability_columns,
        }
        for summary in summaries
        if summary.readable and summary.missing_traceability_columns
    ]
    blocking = bool(missing_by_file)
    return ReadinessCheck(
        name="normalized_traceability_schema",
        status=FAIL if blocking else PASS,
        blocking=blocking,
        message="Normalized Parquet schema contains required traceability fields."
        if not blocking
        else "Some normalized Parquet schemas miss required traceability fields.",
        details={
            "required_columns": sorted(REQUIRED_TRACEABILITY_COLUMNS),
            "missing_by_file": missing_by_file,
        },
    )


def _check_label_columns(summaries: list[_ParquetSummary]) -> ReadinessCheck:
    missing_by_file = [
        {
            "artifact_id": summary.artifact.artifact_id,
            "path": summary.path,
            "missing_columns": summary.missing_label_columns,
        }
        for summary in summaries
        if summary.readable and summary.missing_label_columns
    ]
    null_label_markers = [
        {
            "artifact_id": summary.artifact.artifact_id,
            "path": summary.path,
            "label_status_values": summary.label_status_values,
            "label_source_values": summary.label_source_values,
        }
        for summary in summaries
        if summary.readable
        and (
            summary.label_status_values.get("<NULL>", 0) > 0
            or summary.label_source_values.get("<NULL>", 0) > 0
        )
    ]
    unlabeled = [
        {
            "artifact_id": summary.artifact.artifact_id,
            "path": summary.path,
            "label_status_values": summary.label_status_values,
        }
        for summary in summaries
        if summary.readable and summary.label_status_values.get("unlabeled", 0) > 0
    ]
    blocking = bool(missing_by_file or null_label_markers)
    status = FAIL if blocking else (WARN if unlabeled else PASS)
    message = "Labels are present or explicitly marked as unlabeled."
    if blocking:
        message = "Some normalized Parquet files lack required label markers."
    elif unlabeled:
        message = "Some normalized Parquet samples are explicitly marked unlabeled."
    return ReadinessCheck(
        name="labels_present_or_unlabeled",
        status=status,
        blocking=blocking,
        message=message,
        details={
            "required_columns": sorted(REQUIRED_LABEL_COLUMNS),
            "missing_by_file": missing_by_file,
            "null_label_markers": null_label_markers,
            "unlabeled_samples": unlabeled,
        },
    )


def _check_test_fit_policy(rows: list[_ArtifactRow], request: ValidateInputsRequest) -> ReadinessCheck:
    suspicious = []
    if request.role == "TEST":
        for row in rows:
            metadata = row.artifact.metadata_json or {}
            if _metadata_indicates_preprocessing_fit(metadata):
                suspicious.append(
                    {
                        "artifact_id": row.artifact.id,
                        "normalized_path": row.artifact.normalized_path,
                        "metadata": metadata,
                    }
                )
    return ReadinessCheck(
        name="test_not_for_train_preprocessing_fit",
        status=PASS if not suspicious else FAIL,
        blocking=bool(suspicious),
        message="TEST artifacts are not marked for TRAIN preprocessing fit."
        if not suspicious
        else "TEST artifacts contain metadata that looks like preprocessing fit intent.",
        details={
            "role": request.role,
            "fit_allowed": request.role == "TRAIN",
            "suspicious_artifacts": suspicious,
        },
    )


def _metadata_indicates_preprocessing_fit(metadata: dict[str, Any]) -> bool:
    for key in ("fit_preprocessing", "preprocessing_fit", "used_for_train_fit"):
        if bool(metadata.get(key)):
            return True
    for key in ("fit_role", "fitted_on_role", "preprocessing_fit_role"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip().upper() == "TRAIN":
            return True
    return False


def _resolve_storage_root(storage_root: str | Path | None) -> Path:
    raw_value = str(storage_root if storage_root is not None else PATH_DATA_STORAGE).strip()
    if not raw_value:
        raise ValueError("PATH_DATA_STORAGE must be configured for Stage Three validate-inputs.")
    return Path(raw_value).expanduser()


def _resolve_artifact_path(storage_root: Path, artifact_path: str) -> Path:
    path = Path(artifact_path).expanduser()
    if path.is_absolute():
        return path
    return storage_root / path


def _count_statuses(values: Any) -> dict[str, int]:
    counter = Counter(str(value or "<NULL>") for value in values)
    return dict(sorted(counter.items()))


def _statuses_present(counts: dict[str, int], statuses: frozenset[str]) -> bool:
    return any(counts.get(status, 0) > 0 for status in statuses)


def _overall_status(checks: list[ReadinessCheck]) -> str:
    if any(check.status == FAIL and check.blocking for check in checks):
        return FAIL
    if any(check.status in {FAIL, WARN} for check in checks):
        return WARN
    return PASS


def _next_actions(status: str, request: ValidateInputsRequest, blocking_issues: list[str]) -> list[str]:
    if status == PASS:
        return [
            f"Proceed with Stage Three feature extraction for {request.branch}/{request.role}.",
            "Keep preprocessing fit restricted to TRAIN; VALIDATION/TEST may only transform.",
        ]
    if status == WARN:
        return [
            f"Proceed only after accepting warnings for {request.branch}/{request.role}.",
            "Review PARTIAL_SUCCESS/PARTIALLY_PARSED and unlabeled samples before feature extraction.",
        ]
    if blocking_issues:
        return [
            "Do not start downstream Stage Three commands for this branch/role.",
            "Fix blocking catalog, parser, schema, or Parquet issues and rerun validate-inputs.",
        ]
    return ["Rerun validate-inputs after resolving readiness warnings."]
