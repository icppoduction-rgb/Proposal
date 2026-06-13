"""Data quality and leakage checkers for Stage Two artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import DataQualityReport, ModelReadyArtifact, PreprocessingArtifact
from scripts.db.repositories import DataQualityRepository
from scripts.stage_two.duckdb import DuckDBAnalyticsService
from scripts.stage_two.duckdb.service import REQUIRED_COLUMNS, VIEW_PATTERNS
from scripts.stage_two.model_ready import X_FORBIDDEN_COLUMNS
from scripts.stage_two.quality.checks import QualityCheckResult, QualityReportResult


ROLE_VALUES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST", "EXPERIMENTS")
BRANCH_VALUES: tuple[str, ...] = ("dns", "host", "network", "hybrid")


class DataQualityChecker:
    """Run schema, null, duplicate, and role/branch checks over DuckDB views."""

    def __init__(self, analytics_service: DuckDBAnalyticsService) -> None:
        """Initialize the checker with a DuckDB analytics service."""
        self.analytics_service = analytics_service

    def run(self, repository: DataQualityRepository | None = None) -> QualityReportResult:
        """Run data quality checks, save reports, and optionally register them."""
        connection = self.analytics_service.connect()
        try:
            self.analytics_service.create_views(connection)
            checks = [
                *self._required_column_checks(connection),
                *self._null_count_checks(connection),
                *self._duplicate_key_checks(connection),
                *self._role_branch_value_checks(connection),
            ]
        finally:
            connection.close()
        report = build_report("quality", checks, self.analytics_service.storage_root)
        if repository is not None:
            register_quality_report(repository, report)
        return report

    def _required_column_checks(self, connection: duckdb.DuckDBPyConnection) -> list[QualityCheckResult]:
        checks: list[QualityCheckResult] = []
        for view_name, required_columns in REQUIRED_COLUMNS.items():
            columns = set(columns_for(connection, view_name))
            missing = sorted(set(required_columns).difference(columns))
            checks.append(
                QualityCheckResult(
                    check_name=f"required_columns_{view_name}",
                    status="SUCCESS" if not missing else "FAILED",
                    severity="ERROR" if missing else "INFO",
                    rows_total=len(required_columns),
                    rows_failed=len(missing),
                    details={"missing_columns": missing},
                )
            )
        return checks

    def _null_count_checks(self, connection: duckdb.DuckDBPyConnection) -> list[QualityCheckResult]:
        checks: list[QualityCheckResult] = []
        for view_name, required_columns in REQUIRED_COLUMNS.items():
            columns = set(columns_for(connection, view_name))
            present = [column for column in required_columns if column in columns]
            if not present:
                checks.append(QualityCheckResult(f"null_counts_{view_name}", "SUCCESS", "INFO", 0, 0, {}))
                continue
            expressions = ", ".join(
                f"SUM(CASE WHEN {quote_identifier(column)} IS NULL THEN 1 ELSE 0 END) AS {quote_identifier(column)}"
                for column in present
            )
            row = connection.execute(f"SELECT COUNT(*) AS row_count, {expressions} FROM {view_name}").fetchone()
            null_counts = dict(zip(present, row[1:], strict=True))
            failed = sum(int(value or 0) for value in null_counts.values())
            checks.append(
                QualityCheckResult(
                    check_name=f"null_counts_{view_name}",
                    status="SUCCESS" if failed == 0 else "FAILED",
                    severity="ERROR" if failed else "INFO",
                    rows_total=row[0],
                    rows_failed=failed,
                    details={"null_counts": null_counts},
                )
            )
        return checks

    def _duplicate_key_checks(self, connection: duckdb.DuckDBPyConnection) -> list[QualityCheckResult]:
        checks: list[QualityCheckResult] = []
        for view_name, key in (("normalized_all", "event_uid"), ("features_all", "sample_uid"), ("model_ready_all", "sample_uid")):
            columns = set(columns_for(connection, view_name))
            if key not in columns:
                checks.append(QualityCheckResult(f"duplicate_{key}_{view_name}", "SUCCESS", "INFO", 0, 0, {"skipped": "missing key column"}))
                continue
            row = connection.execute(
                f"SELECT COUNT(*) AS rows_total, COUNT(DISTINCT {quote_identifier(key)}) AS distinct_keys FROM {view_name}"
            ).fetchone()
            duplicates = int(row[0] - row[1])
            checks.append(
                QualityCheckResult(
                    check_name=f"duplicate_{key}_{view_name}",
                    status="SUCCESS" if duplicates == 0 else "FAILED",
                    severity="ERROR" if duplicates else "INFO",
                    rows_total=row[0],
                    rows_failed=duplicates,
                    details={"key": key},
                )
            )
        return checks

    def _role_branch_value_checks(self, connection: duckdb.DuckDBPyConnection) -> list[QualityCheckResult]:
        checks: list[QualityCheckResult] = []
        for view_name in VIEW_PATTERNS:
            columns = set(columns_for(connection, view_name))
            checks.extend(value_domain_checks(connection, view_name, columns, "role", ROLE_VALUES))
            checks.extend(value_domain_checks(connection, view_name, columns, "dataset_role", ROLE_VALUES))
            checks.extend(value_domain_checks(connection, view_name, columns, "branch", BRANCH_VALUES))
        return checks


class LeakageChecker:
    """Run leakage checks and block unsafe model-ready artifacts."""

    def __init__(self, analytics_service: DuckDBAnalyticsService, *, session: Session | None = None) -> None:
        """Initialize the checker with DuckDB analytics and optional catalog session."""
        self.analytics_service = analytics_service
        self.session = session

    def run(self, repository: DataQualityRepository | None = None) -> QualityReportResult:
        """Run leakage checks, save reports, and optionally register them."""
        connection = self.analytics_service.connect()
        try:
            self.analytics_service.create_views(connection)
            checks = [
                self._x_forbidden_columns_check(connection),
                self._test_absent_from_train_check(connection),
                self._preprocessing_fit_role_check(),
            ]
        finally:
            connection.close()
        report = build_report("leakage", checks, self.analytics_service.storage_root, failed_severity="CRITICAL")
        if repository is not None:
            register_quality_report(repository, report)
        return report

    def block_model_ready_if_failed(
        self,
        artifact: ModelReadyArtifact,
        report: QualityReportResult,
    ) -> ModelReadyArtifact:
        """Mark a SUCCESS model-ready artifact BLOCKED when leakage checks failed."""
        if report.status == "FAILED" and artifact.status == "SUCCESS":
            artifact.status = "BLOCKED"
        return artifact

    def _x_forbidden_columns_check(self, connection: duckdb.DuckDBPyConnection) -> QualityCheckResult:
        columns = set(columns_for(connection, "model_ready_all"))
        forbidden = sorted(set(X_FORBIDDEN_COLUMNS).intersection(columns))
        if not forbidden:
            return QualityCheckResult("x_forbidden_columns", "SUCCESS", "INFO", 0, 0, {"forbidden_columns": []})
        x_filter = "lower(replace(filename, chr(92), '/')) LIKE '%/tabular/%/x_%'" if "filename" in columns else "TRUE"
        counts: dict[str, int] = {}
        for column in forbidden:
            count = connection.execute(
                f"SELECT COUNT(*) FROM model_ready_all WHERE {x_filter} AND {quote_identifier(column)} IS NOT NULL"
            ).fetchone()[0]
            if count:
                counts[column] = int(count)
        failed = sum(counts.values())
        return QualityCheckResult(
            check_name="x_forbidden_columns",
            status="SUCCESS" if failed == 0 else "FAILED",
            severity="CRITICAL" if failed else "INFO",
            rows_total=failed,
            rows_failed=failed,
            details={"non_null_forbidden_columns": counts},
        )

    def _test_absent_from_train_check(self, connection: duckdb.DuckDBPyConnection) -> QualityCheckResult:
        columns = set(columns_for(connection, "model_ready_all"))
        if "dataset_role" not in columns:
            return QualityCheckResult("test_absent_from_train", "SUCCESS", "INFO", 0, 0, {"skipped": "dataset_role not present"})
        train_filter = "lower(replace(filename, chr(92), '/')) LIKE '%/train/%'" if "filename" in columns else "role = 'TRAIN'"
        count = connection.execute(
            f"SELECT COUNT(*) FROM model_ready_all WHERE {train_filter} AND dataset_role = 'TEST'"
        ).fetchone()[0]
        return QualityCheckResult(
            check_name="test_absent_from_train",
            status="SUCCESS" if count == 0 else "FAILED",
            severity="CRITICAL" if count else "INFO",
            rows_total=count,
            rows_failed=count,
            details={"rule": "TEST rows must not appear in TRAIN model-ready artifacts"},
        )

    def _preprocessing_fit_role_check(self) -> QualityCheckResult:
        if self.session is None:
            return QualityCheckResult("preprocessing_fit_only_train", "SUCCESS", "INFO", 0, 0, {"skipped": "no catalog session"})
        statement = select(PreprocessingArtifact).where(PreprocessingArtifact.fitted_on_role != "TRAIN")
        rows = list(self.session.execute(statement).scalars())
        failed = len(rows)
        return QualityCheckResult(
            check_name="preprocessing_fit_only_train",
            status="SUCCESS" if failed == 0 else "FAILED",
            severity="CRITICAL" if failed else "INFO",
            rows_total=failed,
            rows_failed=failed,
            details={"artifact_ids": [row.id for row in rows]},
        )


def value_domain_checks(
    connection: duckdb.DuckDBPyConnection,
    view_name: str,
    columns: set[str],
    column: str,
    allowed_values: tuple[str, ...],
) -> list[QualityCheckResult]:
    """Return value-domain check for a role/branch column when present."""
    if column not in columns:
        return []
    placeholders = ", ".join(f"'{value}'" for value in allowed_values)
    count = connection.execute(
        f"SELECT COUNT(*) FROM {view_name} WHERE {quote_identifier(column)} IS NOT NULL "
        f"AND {quote_identifier(column)} NOT IN ({placeholders})"
    ).fetchone()[0]
    return [
        QualityCheckResult(
            check_name=f"{column}_values_{view_name}",
            status="SUCCESS" if count == 0 else "FAILED",
            severity="ERROR" if count else "INFO",
            rows_total=count,
            rows_failed=count,
            details={"allowed_values": list(allowed_values)},
        )
    ]


def build_report(
    check_group: str,
    checks: list[QualityCheckResult],
    storage_root: Path,
    *,
    failed_severity: str = "ERROR",
) -> QualityReportResult:
    """Build and save an EN/RU JSON quality report."""
    failed = [check for check in checks if check.status != "SUCCESS"]
    status = "FAILED" if failed else "SUCCESS"
    severity = failed_severity if failed else "INFO"
    report = QualityReportResult(check_group, status, severity, {}, checks)
    report_paths = save_quality_report(report, storage_root)
    return QualityReportResult(check_group, status, severity, report_paths, checks)


def save_quality_report(report: QualityReportResult, storage_root: Path) -> dict[str, str]:
    """Save the same JSON quality report under RU and EN report directories."""
    paths: dict[str, str] = {}
    for language in ("en", "ru"):
        report_dir = storage_root / "reports" / language / "stage-two" / report.check_group
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / f"{report.check_group}_report.json"
        payload = asdict(report)
        payload["report_paths"] = {}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        paths[language] = path.relative_to(storage_root).as_posix()
    return paths


def register_quality_report(
    repository: DataQualityRepository,
    report: QualityReportResult,
) -> DataQualityReport:
    """Register an aggregate quality/leakage report in PostgreSQL catalog."""
    return repository.create_report(
        report_uid=uuid4(),
        artifact_type="model_ready" if report.check_group == "leakage" else "catalog",
        artifact_id=None,
        check_group=report.check_group,
        check_name=f"{report.check_group}_checks",
        status=report.status,
        severity=report.severity,
        rows_total=sum(check.rows_total or 0 for check in report.checks),
        rows_valid=sum((check.rows_total or 0) - (check.rows_failed or 0) for check in report.checks),
        rows_failed=sum(check.rows_failed or 0 for check in report.checks),
        missing_values_count=sum(
            check.rows_failed or 0 for check in report.checks if check.check_name.startswith("null_counts")
        ),
        duplicate_rows_count=sum(
            check.rows_failed or 0 for check in report.checks if check.check_name.startswith("duplicate_")
        ),
        schema_mismatch_count=sum(
            check.rows_failed or 0 for check in report.checks if "required_columns" in check.check_name
        ),
        leakage_issue_count=sum(
            check.rows_failed or 0 for check in report.checks if report.check_group == "leakage"
        ),
        label_distribution_json=None,
        timestamp_coverage_json=None,
        details_json=asdict(report),
        report_path=report.report_paths.get("en"),
    )


def columns_for(connection: duckdb.DuckDBPyConnection, view_name: str) -> list[str]:
    """Return DuckDB view column names."""
    rows = connection.execute(f"DESCRIBE SELECT * FROM {view_name}").fetchall()
    return [row[0] for row in rows]


def quote_identifier(value: str) -> str:
    """Quote a SQL identifier for DuckDB."""
    return '"' + value.replace('"', '""') + '"'
