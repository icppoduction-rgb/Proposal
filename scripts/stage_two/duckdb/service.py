"""DuckDB analytics checks over Stage Two Parquet artifacts."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb
import pyarrow.parquet as pq

from config import (
    DUCKDB_DATABASE_RELATIVE,
    PARQUET_FEATURES_RELATIVE,
    PARQUET_MODEL_READY_RELATIVE,
    PARQUET_NORMALIZED_RELATIVE,
    PATH_DATA_STORAGE,
    REPORTS_EN_STAGE_TWO_QUALITY,
    STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE,
    STAGE_TWO_DUCKDB_MEMORY_LIMIT,
    STAGE_TWO_DUCKDB_THREADS,
    TEMP_DATA_DUCKDB_RELATIVE,
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
ProgressCallback = Callable[[str, dict[str, Any]], None]
READ_PARQUET_CHUNK_SIZE = 512


@dataclass(frozen=True)
class DuckDBRuntimeSettings:
    """Bounded DuckDB runtime settings for large Stage Two Parquet scans."""

    memory_limit: str = STAGE_TWO_DUCKDB_MEMORY_LIMIT
    threads: int = STAGE_TWO_DUCKDB_THREADS
    temp_directory: str | Path | None = None
    max_temp_directory_size: str = STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE


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


@dataclass(frozen=True)
class ParquetLayerStats:
    """Streaming metadata summary for one Stage Two Parquet layer."""

    view_name: str
    file_count: int
    row_count: int
    columns: frozenset[str]
    groups: dict[tuple[str, ...], int]
    group_columns: tuple[str, ...]
    metadata_errors: tuple[dict[str, str], ...] = ()


class DuckDBAnalyticsService:
    """Create DuckDB views and run analytics checks over Parquet files."""

    def __init__(
        self,
        *,
        storage_root: str | Path | None = None,
        database_path: str | Path | None = None,
        runtime_settings: DuckDBRuntimeSettings | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize the service with storage and DuckDB database paths."""
        self.storage_root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
        if not str(self.storage_root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured for DuckDB analytics.")
        self.database_path = Path(database_path) if database_path is not None else self.storage_root / DUCKDB_DATABASE_RELATIVE
        self.runtime_settings = runtime_settings or DuckDBRuntimeSettings()
        self.progress_callback = progress_callback

    def create_views(
        self,
        connection: duckdb.DuckDBPyConnection | None = None,
        *,
        view_names: tuple[str, ...] | None = None,
    ) -> None:
        """Create normalized_all, features_all, and model_ready_all DuckDB views."""
        owns_connection = connection is None
        connection = connection or self.connect()
        selected_view_names = view_names or tuple(VIEW_PATTERNS)
        try:
            self._emit("create_views_started", view_count=len(selected_view_names))
            for view_name in selected_view_names:
                pattern = VIEW_PATTERNS[view_name]
                files = self._matching_parquet_files(pattern)
                self._emit(
                    "view_started",
                    view_name=view_name,
                    pattern=pattern,
                    file_count=len(files),
                )
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
                self._emit(
                    "view_finished",
                    view_name=view_name,
                    file_count=len(files),
                    status="SUCCESS",
                )
            self._emit("create_views_finished", view_count=len(selected_view_names))
        finally:
            if owns_connection:
                connection.close()

    def run_checks(self, *, report_name: str = "duckdb_analytics_report.json") -> DuckDBAnalyticsReport:
        """Run row-count, missing-column, split-contamination, and schema checks."""
        checks: list[DuckDBCheckResult] = []
        self._emit("run_started", runtime_settings=self.runtime_settings_payload())
        layer_stats = self._collect_layer_stats()
        checks.extend(
            self._run_check_group("row_count_checks", lambda: self._row_count_checks_from_stats(layer_stats))
        )
        checks.extend(
            self._run_check_group(
                "missing_required_column_checks",
                lambda: self._missing_required_column_checks_from_stats(layer_stats),
            )
        )
        checks.extend(
            self._run_check_group(
                "split_contamination",
                lambda: [self._split_contamination_check_chunked(layer_stats["model_ready_all"])],
            )
        )
        checks.extend(
            self._run_check_group(
                "schema_mismatch",
                lambda: [self._schema_mismatch_check_from_stats(layer_stats)],
            )
        )
        status = "SUCCESS" if all(check.status == "SUCCESS" for check in checks) else "FAILED"
        self._emit("report_started", report_name=report_name, status=status)
        report_path = self.save_report(DuckDBAnalyticsReport(status=status, report_path="", checks=checks), report_name)
        self._emit("report_finished", report_name=report_name, report_path=report_path, status=status)
        self._emit("run_finished", status=status, check_count=len(checks), report_path=report_path)
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
        connection = duckdb.connect(str(self.database_path))
        self._configure_connection(connection)
        return connection

    def runtime_settings_payload(self) -> dict[str, Any]:
        """Return runtime settings as a JSON-serializable payload."""
        settings = self.runtime_settings
        temp_directory = self._temp_directory()
        return {
            "memory_limit": settings.memory_limit,
            "threads": settings.threads,
            "temp_directory": str(temp_directory) if temp_directory is not None else None,
            "max_temp_directory_size": settings.max_temp_directory_size,
        }

    def _configure_connection(self, connection: duckdb.DuckDBPyConnection) -> None:
        settings = self.runtime_settings
        if settings.threads <= 0:
            raise ValueError("DuckDB runtime threads must be positive")
        connection.execute(f"SET memory_limit='{_sql_string(settings.memory_limit)}'")
        connection.execute(f"SET threads={settings.threads}")
        connection.execute("SET preserve_insertion_order=false")
        temp_directory = self._temp_directory()
        if temp_directory is not None:
            temp_directory.mkdir(parents=True, exist_ok=True)
            connection.execute(f"SET temp_directory='{_sql_string(temp_directory.as_posix())}'")
        connection.execute(f"SET max_temp_directory_size='{_sql_string(settings.max_temp_directory_size)}'")

    def _temp_directory(self) -> Path | None:
        configured = self.runtime_settings.temp_directory
        if configured is not None:
            return Path(configured).expanduser()
        return self.storage_root / TEMP_DATA_DUCKDB_RELATIVE

    def _run_check_group(
        self,
        check_name: str,
        callback: Callable[[], list[DuckDBCheckResult]],
    ) -> list[DuckDBCheckResult]:
        self._emit("check_started", check_name=check_name)
        checks = callback()
        failed = sum(1 for check in checks if check.status != "SUCCESS")
        self._emit(
            "check_finished",
            check_name=check_name,
            check_count=len(checks),
            failed_count=failed,
        )
        return checks

    def _collect_layer_stats(self) -> dict[str, ParquetLayerStats]:
        stats: dict[str, ParquetLayerStats] = {}
        for view_name, pattern in VIEW_PATTERNS.items():
            files = self._matching_parquet_files(pattern)
            self._emit("view_started", view_name=view_name, pattern=pattern, file_count=len(files))
            stats[view_name] = self._collect_one_layer_stats(view_name, files)
            self._emit(
                "view_finished",
                view_name=view_name,
                file_count=len(files),
                status="SUCCESS" if not stats[view_name].metadata_errors else "FAILED",
            )
        return stats

    def _collect_one_layer_stats(self, view_name: str, files: list[Path]) -> ParquetLayerStats:
        columns: set[str] = set()
        groups: Counter[tuple[str, ...]] = Counter()
        metadata_errors: list[dict[str, str]] = []
        row_count = 0
        group_columns = _metadata_group_columns(view_name)
        total = len(files)
        if total:
            columns.add("filename")
        for index, path in enumerate(files, start=1):
            try:
                metadata = pq.read_metadata(path)
                file_rows = int(metadata.num_rows)
                row_count += file_rows
                columns.update(str(name) for name in metadata.schema.names)
                groups[_metadata_group_key(view_name, path, self.storage_root)] += file_rows
            except Exception as exc:
                metadata_errors.append({"path": str(path), "error": _exception_message(exc)})
            if index == total or index % 1000 == 0:
                self._emit(
                    "view_progress",
                    view_name=view_name,
                    current=index,
                    total=total,
                    rows_seen=row_count,
                    metadata_errors=len(metadata_errors),
                )
        return ParquetLayerStats(
            view_name=view_name,
            file_count=total,
            row_count=row_count,
            columns=frozenset(columns),
            groups=dict(groups),
            group_columns=group_columns,
            metadata_errors=tuple(metadata_errors),
        )

    def _row_count_checks_from_stats(
        self,
        layer_stats: dict[str, ParquetLayerStats],
    ) -> list[DuckDBCheckResult]:
        checks: list[DuckDBCheckResult] = []
        for view_name in VIEW_PATTERNS:
            stats = layer_stats[view_name]
            checks.append(
                DuckDBCheckResult(
                    check_name=f"row_counts_{view_name}",
                    status="SUCCESS" if not stats.metadata_errors else "FAILED",
                    rows_total=stats.row_count,
                    rows_failed=len(stats.metadata_errors),
                    details={
                        "mode": "parquet_metadata",
                        "file_count": stats.file_count,
                        "group_columns": list(stats.group_columns),
                        "rows": [list(key) + [count] for key, count in sorted(stats.groups.items())],
                        "metadata_errors": list(stats.metadata_errors[:20]),
                        "metadata_error_count": len(stats.metadata_errors),
                    },
                )
            )
        return checks

    def _missing_required_column_checks_from_stats(
        self,
        layer_stats: dict[str, ParquetLayerStats],
    ) -> list[DuckDBCheckResult]:
        checks: list[DuckDBCheckResult] = []
        for view_name, required_columns in REQUIRED_COLUMNS.items():
            stats = layer_stats[view_name]
            missing = sorted(set(required_columns).difference(stats.columns))
            if stats.file_count == 0:
                missing = []
            failed = len(missing) + len(stats.metadata_errors)
            checks.append(
                DuckDBCheckResult(
                    check_name=f"missing_required_columns_{view_name}",
                    status="SUCCESS" if failed == 0 else "FAILED",
                    rows_total=len(required_columns) + len(stats.metadata_errors),
                    rows_failed=failed,
                    details={
                        "mode": "parquet_metadata",
                        "missing_columns": missing,
                        "metadata_error_count": len(stats.metadata_errors),
                    },
                )
            )
        return checks

    def _split_contamination_check_chunked(self, stats: ParquetLayerStats) -> DuckDBCheckResult:
        if stats.file_count == 0 or not {"role", "dataset_role"}.issubset(stats.columns):
            count = 0
        else:
            count = self._count_model_ready_rows(
                "role = 'TRAIN' AND dataset_role = 'TEST'",
                required_columns=("role", "dataset_role"),
            )
        return DuckDBCheckResult(
            check_name="split_contamination",
            status="SUCCESS" if count == 0 else "FAILED",
            rows_total=count,
            rows_failed=count,
            details={"rule": "no TEST rows in TRAIN model-ready artifacts", "mode": "chunked_read_parquet"},
        )

    def _schema_mismatch_check_from_stats(
        self,
        layer_stats: dict[str, ParquetLayerStats],
    ) -> DuckDBCheckResult:
        missing_by_view: dict[str, list[str]] = {}
        metadata_errors: dict[str, int] = {}
        for view_name, required_columns in REQUIRED_COLUMNS.items():
            stats = layer_stats[view_name]
            missing = sorted(set(required_columns).difference(stats.columns))
            if stats.file_count == 0:
                missing = []
            if missing:
                missing_by_view[view_name] = missing
            if stats.metadata_errors:
                metadata_errors[view_name] = len(stats.metadata_errors)
        mismatch_count = sum(len(columns) for columns in missing_by_view.values()) + sum(metadata_errors.values())
        return DuckDBCheckResult(
            check_name="schema_mismatch",
            status="SUCCESS" if mismatch_count == 0 else "FAILED",
            rows_total=sum(len(columns) for columns in REQUIRED_COLUMNS.values()) + sum(metadata_errors.values()),
            rows_failed=mismatch_count,
            details={
                "mode": "parquet_metadata",
                "missing_by_view": missing_by_view,
                "metadata_error_count_by_view": metadata_errors,
            },
        )

    def _count_model_ready_rows(
        self,
        condition_sql: str,
        *,
        required_columns: tuple[str, ...],
    ) -> int:
        files = self._matching_parquet_files(VIEW_PATTERNS["model_ready_all"])
        if not files:
            return 0
        count = 0
        connection = self.connect()
        try:
            for index, chunk in enumerate(_chunks(files, READ_PARQUET_CHUNK_SIZE), start=1):
                relation_sql = _read_parquet_files_sql(chunk)
                query = f"SELECT COUNT(*) FROM {relation_sql} WHERE {condition_sql}"
                try:
                    count += int(connection.execute(query).fetchone()[0])
                except duckdb.BinderException:
                    return 0
                self._emit(
                    "chunk_progress",
                    check_name="split_contamination",
                    current=index,
                    total=(len(files) + READ_PARQUET_CHUNK_SIZE - 1) // READ_PARQUET_CHUNK_SIZE,
                    required_columns=list(required_columns),
                )
        finally:
            connection.close()
        return count

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
                        regexp_extract(filename, '[/\\\\](TRAIN|VALIDATION|TEST)[/\\\\]', 1) AS role_from_path,
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

    def _emit(self, event: str, **payload: Any) -> None:
        if self.progress_callback is not None:
            self.progress_callback(event, payload)


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


def _read_parquet_files_sql(files: list[Path]) -> str:
    quoted_files = ", ".join(f"'{_sql_string(path.as_posix())}'" for path in files)
    return f"read_parquet([{quoted_files}], union_by_name = true, filename = true)"


def _metadata_group_columns(view_name: str) -> tuple[str, ...]:
    if view_name == "features_all":
        return ("feature_group_from_path", "role_from_path")
    if view_name == "model_ready_all":
        return ("artifact_type_from_path", "branch_from_path", "role_from_path")
    return ("branch_from_path", "role_from_path")


def _metadata_group_key(view_name: str, path: Path, storage_root: Path) -> tuple[str, ...]:
    try:
        relative_parts = path.relative_to(storage_root).parts
    except ValueError:
        relative_parts = path.parts
    if view_name == "features_all":
        base = len(Path(PARQUET_FEATURES_RELATIVE).parts)
        return _safe_parts(relative_parts, base, 2)
    if view_name == "model_ready_all":
        base = len(Path(PARQUET_MODEL_READY_RELATIVE).parts)
        return _safe_parts(relative_parts, base, 3)
    base = len(Path(PARQUET_NORMALIZED_RELATIVE).parts)
    return _safe_parts(relative_parts, base, 2)


def _safe_parts(parts: tuple[str, ...], start: int, count: int) -> tuple[str, ...]:
    values = parts[start : start + count]
    if len(values) < count:
        values = (*values, *(("<unknown>",) * (count - len(values))))
    return tuple(values)


def _chunks(values: list[Path], size: int) -> list[list[Path]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__


def _empty_view_columns(view_name: str) -> tuple[str, ...]:
    """Return stable placeholder columns for empty Parquet views."""
    return tuple(dict.fromkeys((*EMPTY_VIEW_COLUMNS, *REQUIRED_COLUMNS.get(view_name, ()))))
