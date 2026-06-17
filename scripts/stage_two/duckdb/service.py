"""DuckDB analytics checks over Stage Two Parquet artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb

from config import (
    DUCKDB_DATABASE_RELATIVE,
    PARQUET_FEATURES_RELATIVE,
    PARQUET_MODEL_READY_RELATIVE,
    PARQUET_NORMALIZED_RELATIVE,
    PATH_DATA_STORAGE,
    REPORTS_EN_STAGE_TWO_QUALITY,
)
from scripts.db.models import DataQualityReport
from scripts.db.repositories import DataQualityRepository


VIEW_PATTERNS: dict[str, str] = {
    "normalized_all": f"{PARQUET_NORMALIZED_RELATIVE}/**/*.parquet",
    "features_all": f"{PARQUET_FEATURES_RELATIVE}/**/*.parquet",
    "model_ready_all": f"{PARQUET_MODEL_READY_RELATIVE}/**/*.parquet",
}
EMPTY_VIEW_COLUMNS: tuple[str, ...] = ("role", "branch", "dataset_role", "feature_group", "data_type")
REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "normalized_all": ("event_uid", "dataset_role", "branch", "source_file_path"),
    "features_all": ("role", "branch", "feature_group"),
    "model_ready_all": ("filename",),
}


@dataclass(frozen=True)
class DuckDBCheckResult:
    """One DuckDB analytics check result."""

    check_name: str
    status: str
    rows_total: int | None = None
    rows_failed: int | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class DuckDBAnalyticsReport:
    """Serializable report for DuckDB checks over Parquet."""

    status: str
    report_path: str
    checks: list[DuckDBCheckResult]


class DuckDBAnalyticsService:
    """Create DuckDB views and run analytics checks over Parquet files."""

    def __init__(
        self,
        *,
        storage_root: str | Path | None = None,
        database_path: str | Path | None = None,
    ) -> None:
        """Initialize the service with storage and DuckDB database paths."""
        self.storage_root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
        if not str(self.storage_root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured for DuckDB analytics.")
        self.database_path = Path(database_path) if database_path is not None else self.storage_root / DUCKDB_DATABASE_RELATIVE

    def create_views(self, connection: duckdb.DuckDBPyConnection | None = None) -> None:
        """Create normalized_all, features_all, and model_ready_all DuckDB views."""
        owns_connection = connection is None
        connection = connection or self.connect()
        try:
            for view_name, pattern in VIEW_PATTERNS.items():
                files = self._matching_parquet_files(pattern)
                if files:
                    glob_path = (self.storage_root / pattern).as_posix()
                    connection.execute(
                        f"CREATE OR REPLACE VIEW {view_name} AS "
                        f"SELECT * FROM read_parquet('{_sql_string(glob_path)}', union_by_name = true, filename = true)"
                    )
                else:
                    empty_columns = ", ".join(
                        f"NULL::VARCHAR AS {column}"
                        for column in _empty_view_columns(view_name)
                    )
                    connection.execute(
                        f"CREATE OR REPLACE VIEW {view_name} AS SELECT {empty_columns} WHERE false"
                    )
        finally:
            if owns_connection:
                connection.close()

    def run_checks(self, *, report_name: str = "duckdb_analytics_report.json") -> DuckDBAnalyticsReport:
        """Run row-count, missing-column, split-contamination, and schema checks."""
        checks: list[DuckDBCheckResult] = []
        connection = self.connect()
        try:
            self.create_views(connection)
            checks.extend(self._row_count_checks(connection))
            checks.extend(self._missing_required_column_checks(connection))
            checks.append(self._split_contamination_check(connection))
            checks.append(self._schema_mismatch_check(connection))
        finally:
            connection.close()
        status = "SUCCESS" if all(check.status == "SUCCESS" for check in checks) else "FAILED"
        report_path = self.save_report(DuckDBAnalyticsReport(status=status, report_path="", checks=checks), report_name)
        return DuckDBAnalyticsReport(status=status, report_path=report_path, checks=checks)

    def save_report(self, report: DuckDBAnalyticsReport, report_name: str) -> str:
        """Persist a DuckDB analytics JSON report under PATH_DATA_STORAGE reports."""
        report_dir = self.storage_root / REPORTS_EN_STAGE_TWO_QUALITY
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / report_name
        payload = asdict(report)
        payload["report_path"] = path.relative_to(self.storage_root).as_posix()
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return payload["report_path"]

    def register_report(
        self,
        repository: DataQualityRepository,
        report: DuckDBAnalyticsReport,
    ) -> DataQualityReport:
        """Register the aggregate DuckDB report in data_quality_reports."""
        failed_checks = [check for check in report.checks if check.status != "SUCCESS"]
        return repository.create_report(
            report_uid=uuid4(),
            artifact_type="catalog",
            artifact_id=None,
            check_group="duckdb",
            check_name="analytics_checks",
            status=report.status,
            severity="ERROR" if failed_checks else "INFO",
            rows_total=sum(check.rows_total or 0 for check in report.checks),
            rows_valid=sum((check.rows_total or 0) - (check.rows_failed or 0) for check in report.checks),
            rows_failed=sum(check.rows_failed or 0 for check in report.checks),
            missing_values_count=None,
            duplicate_rows_count=None,
            schema_mismatch_count=sum(
                check.rows_failed or 0 for check in report.checks if check.check_name == "schema_mismatch"
            ),
            leakage_issue_count=sum(
                check.rows_failed or 0 for check in report.checks if check.check_name == "split_contamination"
            ),
            label_distribution_json=None,
            timestamp_coverage_json=None,
            details_json=asdict(report),
            report_path=report.report_path,
        )

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Open a DuckDB connection."""
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.database_path))

    def _row_count_checks(self, connection: duckdb.DuckDBPyConnection) -> list[DuckDBCheckResult]:
        checks: list[DuckDBCheckResult] = []
        for view_name in VIEW_PATTERNS:
            columns = self._columns(connection, view_name)
            group_columns = [column for column in ("role", "dataset_role", "branch") if column in columns]
            if not group_columns and "filename" in columns:
                rows = connection.execute(
                    f"""
                    SELECT
                        regexp_extract(filename, '[/\\\\](dns|host|network|hybrid)[/\\\\]', 1) AS branch_from_path,
                        regexp_extract(filename, '[/\\\\](TRAIN|VALIDATION|TEST|EXPERIMENTS)[/\\\\]', 1) AS role_from_path,
                        COUNT(*) AS row_count
                    FROM {view_name}
                    GROUP BY branch_from_path, role_from_path
                    """
                ).fetchall()
                checks.append(
                    DuckDBCheckResult(
                        check_name=f"row_counts_{view_name}",
                        status="SUCCESS",
                        rows_total=sum(row[-1] for row in rows),
                        rows_failed=0,
                        details={"group_columns": ["branch_from_path", "role_from_path"], "rows": [list(row) for row in rows]},
                    )
                )
                continue
            if not group_columns:
                count = connection.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
                checks.append(DuckDBCheckResult(f"row_counts_{view_name}", "SUCCESS", count, 0, {"groups": []}))
                continue
            group_sql = ", ".join(group_columns)
            rows = connection.execute(
                f"SELECT {group_sql}, COUNT(*) AS row_count FROM {view_name} GROUP BY {group_sql}"
            ).fetchall()
            checks.append(
                DuckDBCheckResult(
                    check_name=f"row_counts_{view_name}",
                    status="SUCCESS",
                    rows_total=sum(row[-1] for row in rows),
                    rows_failed=0,
                    details={"group_columns": group_columns, "rows": [list(row) for row in rows]},
                )
            )
        return checks

    def _missing_required_column_checks(self, connection: duckdb.DuckDBPyConnection) -> list[DuckDBCheckResult]:
        checks: list[DuckDBCheckResult] = []
        for view_name, required_columns in REQUIRED_COLUMNS.items():
            columns = set(self._columns(connection, view_name))
            missing = sorted(set(required_columns).difference(columns))
            checks.append(
                DuckDBCheckResult(
                    check_name=f"missing_required_columns_{view_name}",
                    status="SUCCESS" if not missing else "FAILED",
                    rows_total=len(required_columns),
                    rows_failed=len(missing),
                    details={"missing_columns": missing},
                )
            )
        return checks

    def _split_contamination_check(self, connection: duckdb.DuckDBPyConnection) -> DuckDBCheckResult:
        columns = set(self._columns(connection, "model_ready_all"))
        if {"role", "dataset_role"}.issubset(columns):
            count = connection.execute(
                "SELECT COUNT(*) FROM model_ready_all WHERE role = 'TRAIN' AND dataset_role = 'TEST'"
            ).fetchone()[0]
        else:
            count = 0
        return DuckDBCheckResult(
            check_name="split_contamination",
            status="SUCCESS" if count == 0 else "FAILED",
            rows_total=count,
            rows_failed=count,
            details={"rule": "no TEST rows in TRAIN model-ready artifacts"},
        )

    def _schema_mismatch_check(self, connection: duckdb.DuckDBPyConnection) -> DuckDBCheckResult:
        missing_by_view: dict[str, list[str]] = {}
        for view_name, required_columns in REQUIRED_COLUMNS.items():
            columns = set(self._columns(connection, view_name))
            missing = sorted(set(required_columns).difference(columns))
            if missing:
                missing_by_view[view_name] = missing
        mismatch_count = sum(len(columns) for columns in missing_by_view.values())
        return DuckDBCheckResult(
            check_name="schema_mismatch",
            status="SUCCESS" if mismatch_count == 0 else "FAILED",
            rows_total=sum(len(columns) for columns in REQUIRED_COLUMNS.values()),
            rows_failed=mismatch_count,
            details={"missing_by_view": missing_by_view},
        )

    def _columns(self, connection: duckdb.DuckDBPyConnection, view_name: str) -> list[str]:
        rows = connection.execute(f"DESCRIBE SELECT * FROM {view_name}").fetchall()
        return [row[0] for row in rows]

    def _matching_parquet_files(self, pattern: str) -> list[Path]:
        relative_pattern = pattern.replace("**/*.parquet", "")
        root = self.storage_root / relative_pattern
        if not root.exists():
            return []
        return list(root.rglob("*.parquet"))


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def _empty_view_columns(view_name: str) -> tuple[str, ...]:
    """Return stable placeholder columns for empty Parquet views."""
    return tuple(dict.fromkeys((*EMPTY_VIEW_COLUMNS, *REQUIRED_COLUMNS.get(view_name, ()))))
