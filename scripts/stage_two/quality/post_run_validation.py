"""Post-run regression gates for Stage Two normalize-format."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import re
from typing import Any

import duckdb
import pyarrow.parquet as pq
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import PATH_DATA_STORAGE, PATH_REPORT
from scripts.db.models import (
    Dataset,
    DatasetFile,
    FeatureArtifact,
    ModelReadyArtifact,
    NormalizedArtifact,
    ParserRun,
    PreprocessingArtifact,
)
from scripts.stage_two.model_ready import X_FORBIDDEN_COLUMNS
from scripts.stage_two.normalization.runner import NormalizeFormatRequest, NormalizeFormatResult
from scripts.stage_two.parsers.base import REQUIRED_NORMALIZED_FIELDS
from scripts.stage_two.quality.checks import QualityCheckResult


BINARY_SOURCE_FORMATS: frozenset[str] = frozenset({"pcap", "pcapng", "cap"})


@dataclass(frozen=True)
class NormalizeFormatValidationReport:
    """Readable post-run quality gate result for one normalize-format command."""

    status: str
    branch: str
    role: str
    source_format: str
    counts: dict[str, Any]
    checks: tuple[QualityCheckResult, ...]
    report_paths: dict[str, str]


def validate_normalize_format_run(
    session: Session,
    *,
    request: NormalizeFormatRequest,
    result: NormalizeFormatResult,
    report_root: str | Path | None = None,
    storage_root: str | Path | None = None,
) -> NormalizeFormatValidationReport:
    """Run regression gates for one normalize-format result and save reports."""
    artifacts = _artifacts_for_result(session, result)
    parser_runs = _parser_runs_for_artifacts(session, artifacts)
    dataset_files = _dataset_files_for_result(session, result)
    counts = _counts(result, artifacts, parser_runs)
    checks = (
        _reconciliation_check(request, counts),
        _split_separation_check(request, artifacts, storage_root=storage_root),
        _schema_drift_check(artifacts, storage_root=storage_root),
        _coverage_check(artifacts, storage_root=storage_root),
        _leakage_check(session, storage_root=storage_root),
        _traceability_check(session, artifacts, dataset_files),
    )
    status = "SUCCESS" if all(check.status == "SUCCESS" for check in checks) else "FAILED"
    report = NormalizeFormatValidationReport(
        status=status,
        branch=request.branch,
        role=request.role,
        source_format=request.source_format,
        counts=counts,
        checks=checks,
        report_paths={},
    )
    report_paths = save_normalize_format_validation_report(report, report_root=report_root)
    return replace(report, report_paths=report_paths)


def save_normalize_format_validation_report(
    report: NormalizeFormatValidationReport,
    *,
    report_root: str | Path | None = None,
) -> dict[str, str]:
    """Save localized markdown plus JSON post-run validation reports."""
    root = Path(report_root or PATH_REPORT)
    base_name = _report_name(report.branch, report.role, report.source_format)
    paths = {
        "ru_markdown": root / "ru" / "stage-two" / "quality" / f"{base_name}.md",
        "en_markdown": root / "en" / "stage-two" / "quality" / f"{base_name}.md",
        "ru_json": root / "ru" / "stage-two" / "quality" / f"{base_name}.json",
        "en_json": root / "en" / "stage-two" / "quality" / f"{base_name}.json",
    }
    payload = asdict(report)
    payload["report_paths"] = {key: str(path) for key, path in paths.items()}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["ru_markdown"].write_text(_render_markdown(report, language="ru"), encoding="utf-8")
    paths["en_markdown"].write_text(_render_markdown(report, language="en"), encoding="utf-8")
    json_payload = json.dumps(payload, indent=2, sort_keys=True, default=str)
    paths["ru_json"].write_text(json_payload + "\n", encoding="utf-8")
    paths["en_json"].write_text(json_payload + "\n", encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def split_contamination_details(
    *,
    expected_branch: str,
    expected_role: str,
    expected_source_format: str,
    observed_branch_values: set[str],
    observed_role_values: set[str],
    observed_source_format_values: set[str],
) -> dict[str, Any]:
    """Return normalized split contamination details for tests and reports."""
    return {
        "expected": {
            "branch": expected_branch,
            "role": expected_role,
            "source_format": expected_source_format,
        },
        "observed": {
            "branch": sorted(observed_branch_values),
            "dataset_role": sorted(observed_role_values),
            "source_format": sorted(observed_source_format_values),
        },
        "contaminated": (
            observed_branch_values.difference({expected_branch})
            or observed_role_values.difference({expected_role})
            or observed_source_format_values.difference({expected_source_format})
        )
        != set(),
    }


def forbidden_x_columns(columns: set[str]) -> tuple[str, ...]:
    """Return forbidden model-ready X columns present in a schema."""
    return tuple(sorted(columns.intersection(X_FORBIDDEN_COLUMNS)))


def trace_chain_errors(
    *,
    artifact: Any | None,
    parser_run: Any | None,
    dataset_file: Any | None,
    dataset: Any | None,
) -> list[str]:
    """Validate normalized artifact -> parser_run -> dataset_file -> dataset links."""
    errors: list[str] = []
    if artifact is None:
        errors.append("normalized_artifact is missing")
        return errors
    if parser_run is None:
        errors.append(f"parser_run id={getattr(artifact, 'parser_run_id', None)} was not found")
        return errors
    if getattr(artifact, "parser_run_id", None) != getattr(parser_run, "id", None):
        errors.append("normalized_artifact.parser_run_id does not match parser_run.id")
    if dataset_file is None:
        errors.append(f"dataset_file id={getattr(parser_run, 'file_id', None)} was not found")
        return errors
    if getattr(parser_run, "file_id", None) != getattr(dataset_file, "id", None):
        errors.append("parser_run.file_id does not match dataset_file.id")
    if getattr(artifact, "file_id", None) != getattr(dataset_file, "id", None):
        errors.append("normalized_artifact.file_id does not match dataset_file.id")
    if dataset is None:
        errors.append(f"dataset id={getattr(dataset_file, 'dataset_id', None)} was not found")
        return errors
    if getattr(dataset_file, "dataset_id", None) != getattr(dataset, "id", None):
        errors.append("dataset_file.dataset_id does not match dataset.id")
    if not getattr(dataset_file, "file_path", None):
        errors.append("dataset_file.file_path is empty")
    errors.extend(_chunk_trace_errors(dataset_file))
    return errors


def _artifacts_for_result(
    session: Session,
    result: NormalizeFormatResult,
) -> list[NormalizedArtifact]:
    artifact_ids = tuple(
        int(file.artifact_id)
        for file in result.files
        if file.artifact_id is not None
    )
    if not artifact_ids:
        return []
    seed_artifacts = list(
        session.execute(
            select(NormalizedArtifact).where(NormalizedArtifact.id.in_(artifact_ids))
        ).scalars()
    )
    parser_run_ids = tuple(sorted({artifact.parser_run_id for artifact in seed_artifacts}))
    if not parser_run_ids:
        return seed_artifacts
    return list(
        session.execute(
            select(NormalizedArtifact)
            .where(NormalizedArtifact.parser_run_id.in_(parser_run_ids))
            .order_by(NormalizedArtifact.id.asc())
        ).scalars()
    )


def _parser_runs_for_artifacts(
    session: Session,
    artifacts: list[NormalizedArtifact],
) -> list[ParserRun]:
    parser_run_ids = tuple(sorted({artifact.parser_run_id for artifact in artifacts}))
    if not parser_run_ids:
        return []
    return list(
        session.execute(
            select(ParserRun).where(ParserRun.id.in_(parser_run_ids)).order_by(ParserRun.id.asc())
        ).scalars()
    )


def _dataset_files_for_result(
    session: Session,
    result: NormalizeFormatResult,
) -> dict[int, DatasetFile]:
    file_ids = tuple(
        sorted({int(file.file_id) for file in result.files if file.file_id is not None})
    )
    if not file_ids:
        return {}
    rows = session.execute(select(DatasetFile).where(DatasetFile.id.in_(file_ids))).scalars()
    return {int(row.id): row for row in rows}


def _counts(
    result: NormalizeFormatResult,
    artifacts: list[NormalizedArtifact],
    parser_runs: list[ParserRun],
) -> dict[str, Any]:
    return {
        "input_files": result.selected,
        "processed_files": result.processed,
        "parsed_files": result.parsed,
        "partial_files": result.partially_parsed,
        "failed_files": result.failed,
        "skipped_files": result.skipped,
        "unsupported_files": result.unsupported,
        "parsed_events": sum(int(run.events_emitted or 0) for run in parser_runs),
        "output_parquet_rows": sum(int(artifact.row_count or 0) for artifact in artifacts),
        "failed_rows": sum(int(run.rows_failed or 0) for run in parser_runs),
        "artifact_count": len(artifacts),
        "parser_run_count": len(parser_runs),
    }


def _reconciliation_check(
    request: NormalizeFormatRequest,
    counts: dict[str, Any],
) -> QualityCheckResult:
    parsed_events = int(counts["parsed_events"])
    output_rows = int(counts["output_parquet_rows"])
    if counts["parser_run_count"] == 0 and counts["artifact_count"] == 0:
        return QualityCheckResult(
            "parsed_events_match_output_rows",
            "SUCCESS",
            "INFO",
            0,
            0,
            {"skipped_reason": "no new parser runs or artifacts were produced"},
        )
    if request.source_format in BINARY_SOURCE_FORMATS and parsed_events == 0:
        return QualityCheckResult(
            "parsed_events_match_output_rows",
            "SUCCESS",
            "INFO",
            output_rows,
            0,
            {"skipped_reason": "exact event reconciliation unavailable for this binary parser run"},
        )
    failed = abs(parsed_events - output_rows)
    return QualityCheckResult(
        "parsed_events_match_output_rows",
        "SUCCESS" if failed == 0 else "FAILED",
        "ERROR" if failed else "INFO",
        parsed_events,
        failed,
        {"parsed_events": parsed_events, "output_rows": output_rows},
    )


def _split_separation_check(
    request: NormalizeFormatRequest,
    artifacts: list[NormalizedArtifact],
    *,
    storage_root: str | Path | None,
) -> QualityCheckResult:
    if not artifacts:
        return QualityCheckResult("split_separation", "SUCCESS", "INFO", 0, 0, {"skipped_reason": "no artifacts"})
    branch_values = {artifact.branch for artifact in artifacts}
    role_values = {artifact.role for artifact in artifacts}
    path_errors = [
        artifact.normalized_path
        for artifact in artifacts
        if f"/{request.branch}/{request.role}/" not in artifact.normalized_path.replace("\\", "/")
    ]
    column_values = _distinct_normalized_values(artifacts, storage_root=storage_root)
    details = split_contamination_details(
        expected_branch=request.branch,
        expected_role=request.role,
        expected_source_format=request.source_format,
        observed_branch_values=branch_values.union(column_values.get("branch", set())),
        observed_role_values=role_values.union(column_values.get("dataset_role", set())),
        observed_source_format_values=column_values.get("source_format", {request.source_format}),
    )
    details["path_errors"] = path_errors
    failed = int(details["contaminated"]) + len(path_errors)
    return QualityCheckResult(
        "split_separation",
        "SUCCESS" if failed == 0 else "FAILED",
        "ERROR" if failed else "INFO",
        len(artifacts),
        failed,
        details,
    )


def _schema_drift_check(
    artifacts: list[NormalizedArtifact],
    *,
    storage_root: str | Path | None,
) -> QualityCheckResult:
    missing_by_artifact: dict[str, list[str]] = {}
    extra_by_artifact: dict[str, list[str]] = {}
    unreadable: dict[str, str] = {}
    root = _storage_root(storage_root)
    for artifact in artifacts:
        path = root / artifact.normalized_path
        try:
            columns = set(pq.ParquetFile(path).schema.names)
        except Exception as exc:
            unreadable[artifact.normalized_path] = str(exc)
            continue
        missing = sorted(REQUIRED_NORMALIZED_FIELDS.difference(columns))
        extra = sorted(columns.difference(REQUIRED_NORMALIZED_FIELDS))
        if missing:
            missing_by_artifact[artifact.normalized_path] = missing
        if extra:
            extra_by_artifact[artifact.normalized_path] = extra
    failed = len(missing_by_artifact) + len(unreadable)
    return QualityCheckResult(
        "schema_drift",
        "SUCCESS" if failed == 0 else "FAILED",
        "ERROR" if failed else "INFO",
        len(artifacts),
        failed,
        {
            "missing_required_columns": missing_by_artifact,
            "extra_columns_summary": extra_by_artifact,
            "unreadable_artifacts": unreadable,
        },
    )


def _coverage_check(
    artifacts: list[NormalizedArtifact],
    *,
    storage_root: str | Path | None,
) -> QualityCheckResult:
    if not artifacts:
        return QualityCheckResult("label_timestamp_coverage", "SUCCESS", "INFO", 0, 0, {"skipped_reason": "no artifacts"})
    try:
        coverage = _coverage_from_parquet(artifacts, storage_root=storage_root)
    except Exception as exc:
        return QualityCheckResult(
            "label_timestamp_coverage",
            "FAILED",
            "ERROR",
            len(artifacts),
            len(artifacts),
            {"error": str(exc)},
        )
    return QualityCheckResult(
        "label_timestamp_coverage",
        "SUCCESS",
        "INFO",
        coverage["rows_total"],
        0,
        coverage,
    )


def _leakage_check(
    session: Session,
    *,
    storage_root: str | Path | None,
) -> QualityCheckResult:
    forbidden_by_artifact: dict[str, list[str]] = {}
    test_train_links: list[dict[str, Any]] = []
    unreadable: dict[str, str] = {}
    root = _storage_root(storage_root)

    x_artifacts = list(
        session.execute(
            select(ModelReadyArtifact)
            .where(ModelReadyArtifact.data_type == "X")
            .order_by(ModelReadyArtifact.id.asc())
        ).scalars()
    )
    for artifact in x_artifacts:
        path = root / artifact.artifact_path
        try:
            columns = set(pq.ParquetFile(path).schema.names)
        except Exception as exc:
            unreadable[artifact.artifact_path] = str(exc)
            continue
        forbidden = forbidden_x_columns(columns)
        if forbidden:
            forbidden_by_artifact[artifact.artifact_path] = list(forbidden)

    rows = session.execute(
        select(ModelReadyArtifact, FeatureArtifact, NormalizedArtifact, ParserRun, DatasetFile)
        .join(FeatureArtifact, ModelReadyArtifact.feature_artifact_id == FeatureArtifact.id)
        .join(NormalizedArtifact, FeatureArtifact.normalized_artifact_id == NormalizedArtifact.id)
        .join(ParserRun, NormalizedArtifact.parser_run_id == ParserRun.id)
        .join(DatasetFile, ParserRun.file_id == DatasetFile.id)
        .where(ModelReadyArtifact.role == "TRAIN", DatasetFile.role == "TEST")
    ).all()
    for model_ready, _feature, normalized, parser_run, dataset_file in rows:
        test_train_links.append(
            {
                "model_ready_artifact_id": model_ready.id,
                "normalized_artifact_id": normalized.id,
                "parser_run_id": parser_run.id,
                "dataset_file_id": dataset_file.id,
            }
        )

    bad_preprocessing = list(
        session.execute(
            select(PreprocessingArtifact).where(PreprocessingArtifact.fitted_on_role != "TRAIN")
        ).scalars()
    )
    failed = len(forbidden_by_artifact) + len(test_train_links) + len(bad_preprocessing)
    return QualityCheckResult(
        "model_ready_leakage",
        "SUCCESS" if failed == 0 else "FAILED",
        "CRITICAL" if failed else "INFO",
        len(x_artifacts),
        failed,
        {
            "x_forbidden_columns": forbidden_by_artifact,
            "test_rows_in_train_artifacts": test_train_links,
            "bad_preprocessing_artifact_ids": [artifact.id for artifact in bad_preprocessing],
            "unreadable_x_artifacts": unreadable,
        },
    )


def _traceability_check(
    session: Session,
    artifacts: list[NormalizedArtifact],
    dataset_files: dict[int, DatasetFile],
) -> QualityCheckResult:
    errors: dict[str, list[str]] = {}
    for artifact in artifacts:
        parser_run = session.get(ParserRun, artifact.parser_run_id)
        dataset_file = dataset_files.get(int(artifact.file_id))
        if dataset_file is None and parser_run is not None:
            dataset_file = session.get(DatasetFile, parser_run.file_id)
        dataset = session.get(Dataset, dataset_file.dataset_id) if dataset_file is not None else None
        artifact_errors = trace_chain_errors(
            artifact=artifact,
            parser_run=parser_run,
            dataset_file=dataset_file,
            dataset=dataset,
        )
        if artifact_errors:
            errors[str(artifact.id)] = artifact_errors
    return QualityCheckResult(
        "normalized_traceability",
        "SUCCESS" if not errors else "FAILED",
        "ERROR" if errors else "INFO",
        len(artifacts),
        len(errors),
        {"broken_chains": errors},
    )


def _chunk_trace_errors(dataset_file: Any) -> list[str]:
    metadata = getattr(dataset_file, "metadata_json", None) or {}
    parent_file_id = metadata.get("parent_file_id") or metadata.get("split_source_file_id")
    if parent_file_id is None:
        return []
    errors: list[str] = []
    if metadata.get("original_source_path") is None and metadata.get("split_source_file_path") is None:
        errors.append("chunk metadata has parent_file_id but no original_source_path")
    if metadata.get("chunk_index") is None and metadata.get("split_part_index") is None:
        errors.append("chunk metadata has parent_file_id but no chunk_index")
    return errors


def _coverage_from_parquet(
    artifacts: list[NormalizedArtifact],
    *,
    storage_root: str | Path | None,
) -> dict[str, Any]:
    relation_sql = _read_parquet_sql(artifacts, storage_root=storage_root)
    connection = duckdb.connect(":memory:")
    try:
        row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS rows_total,
                SUM(CASE WHEN label_status IS NOT NULL THEN 1 ELSE 0 END) AS label_status_rows,
                SUM(CASE WHEN label_status IS NOT NULL AND label_status <> 'unlabeled' THEN 1 ELSE 0 END) AS labeled_rows,
                SUM(CASE WHEN label_binary IS NOT NULL THEN 1 ELSE 0 END) AS label_binary_rows,
                SUM(CASE WHEN timestamp IS NOT NULL THEN 1 ELSE 0 END) AS timestamp_rows,
                SUM(CASE WHEN timestamp_type = 'missing' THEN 1 ELSE 0 END) AS missing_timestamp_rows
            FROM {relation_sql}
            """
        ).fetchone()
    finally:
        connection.close()
    rows_total = int(row[0] or 0)
    return {
        "rows_total": rows_total,
        "label_status_rows": int(row[1] or 0),
        "labeled_rows": int(row[2] or 0),
        "label_binary_rows": int(row[3] or 0),
        "timestamp_rows": int(row[4] or 0),
        "missing_timestamp_rows": int(row[5] or 0),
        "label_coverage_ratio": _ratio(row[1], rows_total),
        "timestamp_coverage_ratio": _ratio(row[4], rows_total),
    }


def _distinct_normalized_values(
    artifacts: list[NormalizedArtifact],
    *,
    storage_root: str | Path | None,
) -> dict[str, set[str]]:
    if not artifacts:
        return {}
    relation_sql = _read_parquet_sql(artifacts, storage_root=storage_root)
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"""
            SELECT
                branch,
                dataset_role,
                source_format
            FROM {relation_sql}
            GROUP BY branch, dataset_role, source_format
            """
        ).fetchall()
    except Exception:
        return {}
    finally:
        connection.close()
    return {
        "branch": {str(row[0]) for row in rows if row[0] is not None},
        "dataset_role": {str(row[1]) for row in rows if row[1] is not None},
        "source_format": {str(row[2]) for row in rows if row[2] is not None},
    }


def _read_parquet_sql(
    artifacts: list[NormalizedArtifact],
    *,
    storage_root: str | Path | None,
) -> str:
    root = _storage_root(storage_root)
    paths = [(root / artifact.normalized_path).as_posix() for artifact in artifacts]
    quoted = ", ".join(f"'{_sql_string(path)}'" for path in paths)
    return f"read_parquet([{quoted}], union_by_name = true)"


def _storage_root(storage_root: str | Path | None) -> Path:
    root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
    if not str(root).strip():
        raise ValueError("PATH_DATA_STORAGE must be configured for post-run validation.")
    return root


def _ratio(value: Any, total: int) -> float | None:
    if total <= 0:
        return None
    return round(float(value or 0) / total, 6)


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def _report_name(branch: str, role: str, source_format: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{branch}_{role}_{source_format}")
    return f"normalize_format_validation_{safe}"


def _render_markdown(report: NormalizeFormatValidationReport, *, language: str) -> str:
    title = (
        "Normalize-format post-run validation"
        if language == "en"
        else "Post-run validation normalize-format"
    )
    status_label = "Status" if language == "en" else "Статус"
    lines = [
        f"# {title}",
        "",
        f"- {status_label}: `{report.status}`",
        f"- branch/role/format: `{report.branch}/{report.role}/{report.source_format}`",
        "",
        "## Counts",
        "",
        "| metric | value |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in report.counts.items())
    lines.extend(["", "## Checks", "", "| check | status | severity | failed |", "| --- | --- | --- | ---: |"])
    lines.extend(
        f"| {check.check_name} | {check.status} | {check.severity} | {check.rows_failed or 0} |"
        for check in report.checks
    )
    lines.extend(
        [
            "",
            "## Details",
            "",
            "```json",
            json.dumps([asdict(check) for check in report.checks], indent=2, sort_keys=True, default=str),
            "```",
            "",
        ]
    )
    return "\n".join(lines)
