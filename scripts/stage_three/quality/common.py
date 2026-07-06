"""Shared primitives for Stage Three quality checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from config import PATH_DATA_STORAGE
from scripts.db.repositories import DataQualityRepository


PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

DB_STATUS_BY_CHECK_STATUS = {
    PASS: "SUCCESS",
    WARN: "PARTIAL_SUCCESS",
    FAIL: "FAILED",
}


@dataclass(frozen=True)
class QualityCheckRecord:
    """One Stage Three quality check result."""

    check_group: str
    check_name: str
    artifact_type: str
    status: str
    severity: str
    message: str
    artifact_id: int | None = None
    blocking: bool = False
    rows_total: int | None = None
    rows_valid: int | None = None
    rows_failed: int | None = None
    missing_values_count: int | None = None
    duplicate_rows_count: int | None = None
    schema_mismatch_count: int | None = None
    leakage_issue_count: int | None = None
    label_distribution: dict[str, Any] | None = None
    timestamp_coverage: dict[str, Any] | None = None
    details: dict[str, Any] = field(default_factory=dict)
    quality_report_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a report-friendly representation."""
        return asdict(self)


def pass_check(
    *,
    check_group: str,
    check_name: str,
    artifact_type: str,
    message: str,
    artifact_id: int | None = None,
    rows_total: int | None = None,
    rows_valid: int | None = None,
    details: dict[str, Any] | None = None,
) -> QualityCheckRecord:
    """Build a successful quality check."""
    return QualityCheckRecord(
        check_group=check_group,
        check_name=check_name,
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        status=PASS,
        severity="INFO",
        message=message,
        rows_total=rows_total,
        rows_valid=rows_valid if rows_valid is not None else rows_total,
        rows_failed=0 if rows_total is not None else None,
        details=details or {},
    )


def warn_check(
    *,
    check_group: str,
    check_name: str,
    artifact_type: str,
    message: str,
    artifact_id: int | None = None,
    rows_total: int | None = None,
    rows_failed: int | None = None,
    missing_values_count: int | None = None,
    duplicate_rows_count: int | None = None,
    schema_mismatch_count: int | None = None,
    leakage_issue_count: int | None = None,
    label_distribution: dict[str, Any] | None = None,
    timestamp_coverage: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> QualityCheckRecord:
    """Build a warning quality check."""
    return QualityCheckRecord(
        check_group=check_group,
        check_name=check_name,
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        status=WARN,
        severity="WARNING",
        message=message,
        rows_total=rows_total,
        rows_valid=(rows_total - rows_failed) if rows_total is not None and rows_failed is not None else None,
        rows_failed=rows_failed,
        missing_values_count=missing_values_count,
        duplicate_rows_count=duplicate_rows_count,
        schema_mismatch_count=schema_mismatch_count,
        leakage_issue_count=leakage_issue_count,
        label_distribution=label_distribution,
        timestamp_coverage=timestamp_coverage,
        details=details or {},
    )


def fail_check(
    *,
    check_group: str,
    check_name: str,
    artifact_type: str,
    message: str,
    artifact_id: int | None = None,
    blocking: bool = True,
    rows_total: int | None = None,
    rows_failed: int | None = None,
    missing_values_count: int | None = None,
    duplicate_rows_count: int | None = None,
    schema_mismatch_count: int | None = None,
    leakage_issue_count: int | None = None,
    label_distribution: dict[str, Any] | None = None,
    timestamp_coverage: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> QualityCheckRecord:
    """Build a failed quality check."""
    return QualityCheckRecord(
        check_group=check_group,
        check_name=check_name,
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        status=FAIL,
        severity="CRITICAL" if blocking else "ERROR",
        message=message,
        blocking=blocking,
        rows_total=rows_total,
        rows_valid=(rows_total - rows_failed) if rows_total is not None and rows_failed is not None else None,
        rows_failed=rows_failed,
        missing_values_count=missing_values_count,
        duplicate_rows_count=duplicate_rows_count,
        schema_mismatch_count=schema_mismatch_count,
        leakage_issue_count=leakage_issue_count,
        label_distribution=label_distribution,
        timestamp_coverage=timestamp_coverage,
        details=details or {},
    )


def overall_status(records: list[QualityCheckRecord]) -> str:
    """Return PASS/WARN/FAIL for a list of checks."""
    if any(record.status == FAIL for record in records):
        return FAIL
    if any(record.status == WARN for record in records):
        return WARN
    return PASS


def register_quality_records(
    repository: DataQualityRepository,
    records: list[QualityCheckRecord],
    *,
    report_path: str | None,
    report_paths: dict[str, str] | None = None,
) -> list[QualityCheckRecord]:
    """Create DataQualityReport rows and return checks with catalog ids."""
    registered: list[QualityCheckRecord] = []
    for record in records:
        db_status = "BLOCKED" if record.status == FAIL and record.blocking else DB_STATUS_BY_CHECK_STATUS[record.status]
        report = repository.create_report(
            report_uid=uuid4(),
            artifact_type=record.artifact_type,
            artifact_id=record.artifact_id,
            check_group=record.check_group,
            check_name=record.check_name,
            status=db_status,
            severity=record.severity,
            rows_total=record.rows_total,
            rows_valid=record.rows_valid,
            rows_failed=record.rows_failed,
            missing_values_count=record.missing_values_count,
            duplicate_rows_count=record.duplicate_rows_count,
            schema_mismatch_count=record.schema_mismatch_count,
            leakage_issue_count=record.leakage_issue_count,
            label_distribution_json=record.label_distribution,
            timestamp_coverage_json=record.timestamp_coverage,
            details_json={
                **record.details,
                "check_status": record.status,
                "message": record.message,
                "blocking": record.blocking,
                "report_paths": report_paths or {},
            },
            report_path=report_path,
        )
        registered.append(replace(record, quality_report_id=int(report.id)))
    return registered


def resolve_artifact_path(path: str, *, storage_root: str | Path | None = None) -> Path:
    """Resolve a catalog path against PATH_DATA_STORAGE when it is relative."""
    resolved = Path(path).expanduser()
    if resolved.is_absolute():
        return resolved
    return Path(storage_root or PATH_DATA_STORAGE).expanduser() / resolved


def parquet_paths_from_catalog_path(path: str, *, storage_root: str | Path | None = None) -> list[Path]:
    """Resolve a file or directory catalog path into Parquet files."""
    resolved = resolve_artifact_path(path, storage_root=storage_root)
    if resolved.is_file():
        return [resolved]
    if resolved.is_dir():
        return sorted(item for item in resolved.glob("*.parquet") if item.is_file())
    return []


def parquet_paths_from_parts(
    metadata_json: dict[str, Any] | None,
    fallback_path: str,
    *,
    storage_root: str | Path | None = None,
) -> list[Path]:
    """Return Parquet part paths from artifact metadata or the fallback artifact path."""
    paths: list[Path] = []
    metadata = metadata_json or {}
    parts = metadata.get("parts")
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("path"), str):
                path = resolve_artifact_path(part["path"], storage_root=storage_root)
                if path.exists():
                    paths.append(path)
    if paths:
        return paths
    return parquet_paths_from_catalog_path(fallback_path, storage_root=storage_root)


def parquet_row_count(paths: list[Path]) -> int:
    """Return total rows using Parquet metadata only."""
    return sum(pq.read_metadata(path).num_rows for path in paths)


def parquet_schema(paths: list[Path]) -> pa.Schema:
    """Return the first readable Parquet schema."""
    if not paths:
        raise FileNotFoundError("no Parquet paths available")
    return pq.read_schema(paths[0])


def duckdb_relation(paths: list[Path]) -> str:
    """Return a DuckDB read_parquet relation for one or more local files."""
    if not paths:
        raise ValueError("paths must not be empty")
    if len(paths) == 1:
        return f"read_parquet({_sql_string(paths[0])})"
    values = ", ".join(_sql_string(path) for path in paths)
    return f"read_parquet([{values}])"


def duckdb_scalar(paths: list[Path], expression: str) -> Any:
    """Execute one scalar aggregate expression over Parquet files."""
    with duckdb.connect(":memory:") as connection:
        return connection.execute(f"SELECT {expression} FROM {duckdb_relation(paths)}").fetchone()[0]


def duckdb_dict(paths: list[Path], sql: str) -> dict[str, int]:
    """Execute a two-column aggregate query and return a string-keyed dictionary."""
    with duckdb.connect(":memory:") as connection:
        rows = connection.execute(sql.format(relation=duckdb_relation(paths))).fetchall()
    return {("null" if key is None else str(key)): int(value) for key, value in rows}


def quoted_identifier(value: str) -> str:
    """Quote a SQL identifier for DuckDB."""
    return '"' + value.replace('"', '""') + '"'


def _sql_string(path: Path) -> str:
    return "'" + path.as_posix().replace("'", "''") + "'"
