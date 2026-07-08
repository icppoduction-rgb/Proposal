"""Console reporting helpers for Stage Three CLI commands."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit, urlunsplit

try:
    from rich.console import Console
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - exercised only without rich installed.
    Console = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]

try:
    import psutil
except ModuleNotFoundError:  # pragma: no cover - depends on optional runtime dependency.
    psutil = None  # type: ignore[assignment]


SECRET_KEYS = ("password", "passwd", "secret", "token", "key", "credential")
BLOCKED_BY_ML_SAFETY = "BLOCKED: artifacts must not be used for ML experiments"


class StageThreeConsoleReporter:
    """Render Stage Three command headers, progress, summaries, and JSON output."""

    def __init__(self, request: Any, *, storage_root: str | os.PathLike[str] | None = None) -> None:
        self.request = request
        self.command = f"stage-three {getattr(request, 'command', 'unknown')}"
        self.json_output = bool(getattr(request, "json_output", False))
        self.verbose = bool(getattr(request, "verbose", False))
        self.quiet = bool(getattr(request, "quiet", False))
        self.storage_root = str(storage_root or "")
        self.started_at = perf_counter()
        self._last_phase: str | None = None
        self._progress = _ProgressState()
        self._console = _make_console(stderr=False)
        self._stderr = _make_console(stderr=True)

    def start(self, fields: dict[str, Any] | None = None) -> None:
        """Print a compact execution header unless quiet or JSON mode suppresses it."""
        if self.json_output or self.quiet:
            return
        header = _clean_mapping(
            {
                "command": self.command,
                **_request_header_fields(self.request),
                "PATH_DATA_STORAGE": self.storage_root,
                **(fields or {}),
            }
        )
        if _rich_available():
            self._console.print(f"[bold]Stage Three {getattr(self.request, 'command', 'unknown')}[/bold]")
            for key, value in header.items():
                self._console.print(f"{key}: {_format_value(_sanitize(value))}")
        else:
            self._console.print(f"Stage Three {getattr(self.request, 'command', 'unknown')}")
            for key, value in header.items():
                self._console.print(f"{key}: {_format_value(_sanitize(value))}")

    def progress_callback(self, payload: dict[str, object]) -> None:
        """Consume extraction progress events and render phase-level progress."""
        self._progress.update(payload)
        if self.json_output:
            if self.verbose:
                self._stderr.print(json.dumps({"progress": _sanitize(payload)}, ensure_ascii=False, default=str))
            return
        if self.quiet:
            return
        phase = str(payload.get("phase") or "unknown")
        if not self.verbose and phase == self._last_phase and payload.get("status") != "end":
            return
        self._last_phase = phase
        summary = self._progress.summary()
        text = (
            f"phase={phase} "
            f"artifacts={summary['processed_artifacts']}/{summary['total_artifacts'] or '?'} "
            f"rows={summary['rows_read']}/{summary['estimated_rows'] or '?'} "
            f"bytes={summary['bytes_read']}/{summary['estimated_bytes'] or '?'} "
            f"feature_rows={summary['rows_written']} "
            f"batches={summary['batches']} "
            f"elapsed={format_duration(self.elapsed_seconds())}"
        )
        if summary["eta_seconds"] is not None:
            text += f" eta={format_duration(float(summary['eta_seconds']))}"
        if summary["mb_per_second"] is not None:
            text += f" throughput={summary['rows_per_second']:.0f} rows/sec, {summary['mb_per_second']:.2f} MB/sec"
        resources = summary.get("resource_snapshot") or {}
        if resources:
            cpu = resources.get("cpu_percent")
            rss = resources.get("rss_gb")
            available = resources.get("available_ram_gb")
            text += f" cpu={cpu if cpu is not None else '?'}% rss_gb={rss if rss is not None else '?'} available_ram_gb={available if available is not None else '?'}"
        self._stderr.print(text)

    def finish(
        self,
        payload: dict[str, Any],
        *,
        summary: dict[str, Any] | None = None,
        tables: list[ConsoleTable] | None = None,
        next_command: str | None = None,
        severity: str | None = None,
    ) -> None:
        """Render final command output."""
        final_payload = self.machine_payload(
            payload,
            summary=summary,
            next_command=next_command,
            severity=severity,
        )
        if self.json_output:
            sys.stdout.write(json.dumps(final_payload, ensure_ascii=False, sort_keys=True, default=str) + "\n")
            return

        display_summary = summary or _default_summary(payload)
        if self.quiet:
            display_summary = {
                key: value
                for key, value in display_summary.items()
                if key in {"status", "report_paths", "artifact_paths", "stage_four_readiness_status", "next"}
            }
        elif self.verbose:
            display_summary = {
                **display_summary,
                "elapsed_seconds": round(self.elapsed_seconds(), 3),
                "progress_summary": self.progress_summary(),
            }
        if _rich_available() and not self.quiet:
            self._console.print("")
            status = final_payload.get("status") or payload.get("status") or "UNKNOWN"
            self._console.print(f"[bold]Status:[/bold] {status}")
        else:
            self._console.print(f"Status: {final_payload.get('status') or payload.get('status') or 'UNKNOWN'}")
        for key, value in _clean_mapping(display_summary).items():
            self._console.print(f"{key}: {_format_value(_sanitize(value))}")
        if tables and not self.quiet:
            for table in tables:
                self.print_table(table)
        blocking = final_payload.get("blocking_issues") or []
        if blocking:
            self._console.print(f"blocking_issues: {_format_value(blocking)}")
        if final_payload.get("severity") == "CRITICAL":
            self._console.print(BLOCKED_BY_ML_SAFETY)
        missing_paths = final_payload.get("missing_printed_paths") or []
        if missing_paths:
            self._console.print(f"WARNING: printed paths do not exist: {_format_value(missing_paths)}")
        if next_command:
            self._console.print(f"Next: {next_command}")

    def error(
        self,
        *,
        phase: str,
        error: BaseException | str,
        suggested_next_command: str | None = None,
        report_written: bool = False,
    ) -> None:
        """Render a concise failure summary."""
        payload = {
            "status": "ERROR",
            "command": self.command,
            "phase": phase,
            "error": str(error),
            "report_written": report_written,
            "blocking_issues": [str(error)],
            "suggested_next_command": suggested_next_command,
        }
        if self.json_output:
            sys.stdout.write(json.dumps(self.machine_payload(payload), ensure_ascii=False, sort_keys=True) + "\n")
            return
        self._console.print(f"Status: ERROR")
        self._console.print(f"phase: {phase}")
        self._console.print(f"error: {str(error)}")
        if not report_written:
            self._console.print("report: not written because the command failed before report creation")
        if suggested_next_command:
            self._console.print(f"Next: {suggested_next_command}")

    def print_table(self, table: "ConsoleTable") -> None:
        """Render a compact table in rich or plain text."""
        if _rich_available() and Table is not None:
            rich_table = Table(title=table.title)
            for column in table.columns:
                rich_table.add_column(column)
            for row in table.rows:
                rich_table.add_row(*[_format_value(_sanitize(cell)) for cell in row])
            self._console.print(rich_table)
            return
        if table.title:
            self._console.print(table.title)
        self._console.print(" | ".join(table.columns))
        self._console.print(" | ".join("---" for _ in table.columns))
        for row in table.rows:
            self._console.print(" | ".join(_format_value(_sanitize(cell)) for cell in row))

    def machine_payload(
        self,
        payload: dict[str, Any],
        *,
        summary: dict[str, Any] | None = None,
        next_command: str | None = None,
        severity: str | None = None,
    ) -> dict[str, Any]:
        """Build the automation-safe command output object."""
        normalized = _sanitize(payload)
        report_paths = _collect_paths(normalized, "report_paths")
        artifact_paths = _collect_artifact_paths(normalized)
        blocking_issues = _collect_blocking_issues(normalized)
        warnings = _collect_warnings(normalized)
        machine = {
            "status": normalized.get("status", "UNKNOWN"),
            "severity": severity or _derive_severity(normalized),
            "command": self.command,
            "experiment_id": normalized.get("experiment_id") or getattr(self.request, "experiment_id", None),
            "elapsed_seconds": round(self.elapsed_seconds(), 3),
            "artifact_paths": artifact_paths,
            "report_paths": report_paths,
            "warnings": warnings,
            "blocking_issues": blocking_issues,
        }
        if summary:
            machine["summary"] = _sanitize(summary)
        if next_command:
            machine["next_command"] = next_command
        missing = [
            path
            for path in [*report_paths.values(), *artifact_paths]
            if isinstance(path, str) and path and not Path(path).exists()
        ]
        if missing:
            machine["missing_printed_paths"] = missing
        return machine

    def elapsed_seconds(self) -> float:
        return perf_counter() - self.started_at

    def progress_summary(self) -> dict[str, Any]:
        return self._progress.summary()


class ConsoleTable:
    """Small table payload independent of rich."""

    def __init__(self, title: str, columns: list[str], rows: list[list[Any]]) -> None:
        self.title = title
        self.columns = columns
        self.rows = rows


class _ProgressState:
    def __init__(self) -> None:
        self.total_artifacts: int | None = None
        self.processed_artifacts = 0
        self.estimated_rows = 0
        self.rows_read = 0
        self.rows_written = 0
        self.batches = 0
        self.estimated_bytes = 0
        self.bytes_read = 0
        self.bytes_written = 0
        self.started_at = perf_counter()
        self.phases: dict[str, int] = {}
        self.phase_seconds: dict[str, float] = {}
        self.current_phase: str | None = None
        self.current_phase_started_at: float | None = None
        self._row_estimate_artifacts: set[str] = set()
        self._byte_estimate_artifacts: set[str] = set()

    def update(self, payload: dict[str, object]) -> None:
        now = perf_counter()
        phase = str(payload.get("phase") or "unknown")
        self._advance_phase(phase, now=now)
        self.phases[phase] = self.phases.get(phase, 0) + 1
        total = payload.get("total_artifacts")
        if isinstance(total, int):
            self.total_artifacts = total
        if payload.get("status") == "end" and payload.get("artifact_id") is not None:
            self.processed_artifacts += 1
        artifact_key = str(payload.get("artifact_id") or f"event-{len(self.phases)}")
        rows_estimate = _int(payload.get("input_rows_estimate"))
        if rows_estimate and artifact_key not in self._row_estimate_artifacts:
            self.estimated_rows += rows_estimate
            self._row_estimate_artifacts.add(artifact_key)
        input_bytes = _int(payload.get("input_bytes"))
        if input_bytes and artifact_key not in self._byte_estimate_artifacts:
            self.estimated_bytes += input_bytes
            self.bytes_read += input_bytes
            self._byte_estimate_artifacts.add(artifact_key)
        self.rows_read += _int(payload.get("rows_read"))
        self.rows_written += _int(payload.get("rows_written"))
        self.batches += _int(payload.get("batch_count"))
        self.bytes_written += _int(payload.get("output_bytes"))
        elapsed = payload.get("elapsed_seconds")
        if payload.get("status") == "end" and isinstance(elapsed, (int, float)) and elapsed > 0:
            self.phase_seconds[phase] = self.phase_seconds.get(phase, 0.0) + float(elapsed)

    def summary(self) -> dict[str, Any]:
        elapsed = max(0.001, perf_counter() - self.started_at)
        mb = (self.bytes_read + self.bytes_written) / (1024 * 1024)
        eta_seconds = None
        if self.total_artifacts and self.processed_artifacts:
            remaining = max(0, self.total_artifacts - self.processed_artifacts)
            eta_seconds = elapsed * (remaining / self.processed_artifacts)
        return {
            "processed_artifacts": self.processed_artifacts,
            "total_artifacts": self.total_artifacts,
            "estimated_rows": self.estimated_rows,
            "rows_read": self.rows_read,
            "rows_written": self.rows_written,
            "batches": self.batches,
            "estimated_bytes": self.estimated_bytes,
            "bytes_read": self.estimated_bytes,
            "bytes_written": self.bytes_written,
            "rows_per_second": self.rows_read / elapsed,
            "mb_per_second": mb / elapsed if mb else None,
            "eta_seconds": eta_seconds,
            "phases": dict(sorted(self.phases.items())),
            "phase_seconds": self._phase_seconds_with_current(),
            "resource_snapshot": _resource_snapshot(),
        }

    def _advance_phase(self, phase: str, *, now: float) -> None:
        if self.current_phase is None:
            self.current_phase = phase
            self.current_phase_started_at = now
            return
        if phase == self.current_phase:
            return
        if self.current_phase_started_at is not None:
            self.phase_seconds[self.current_phase] = (
                self.phase_seconds.get(self.current_phase, 0.0) + max(0.0, now - self.current_phase_started_at)
            )
        self.current_phase = phase
        self.current_phase_started_at = now

    def _phase_seconds_with_current(self) -> dict[str, float]:
        values = dict(self.phase_seconds)
        if self.current_phase is not None and self.current_phase_started_at is not None:
            values[self.current_phase] = values.get(self.current_phase, 0.0) + max(
                0.0,
                perf_counter() - self.current_phase_started_at,
            )
        return {key: round(value, 3) for key, value in sorted(values.items())}


def format_duration(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def quality_table(checks: list[dict[str, Any]], *, title: str = "Checks") -> ConsoleTable:
    rows = [
        [
            check.get("check_name"),
            check.get("status"),
            check.get("severity"),
            check.get("rows_total"),
            check.get("rows_failed"),
            (check.get("details") or {}).get("report_path") or check.get("report_path"),
            "yes" if check.get("blocking") else "no",
        ]
        for check in checks
    ]
    return ConsoleTable(
        title,
        ["check_name", "status", "severity", "rows_total", "rows_failed", "report_path", "blocking"],
        rows,
    )


def leakage_table(checks: list[dict[str, Any]]) -> ConsoleTable:
    names = {
        "x_forbidden_columns",
        "test_absent_from_train",
        "preprocessing_fit_only_train",
        "traceability_chain",
        "balancing_policy",
    }
    rows = []
    for check in checks:
        check_name = str(check.get("check_name") or "")
        if check_name not in names:
            continue
        rows.append(
            [
                check_name,
                check.get("status"),
                check.get("severity"),
                "yes" if check.get("blocking") else "no",
            ]
        )
    return ConsoleTable(
        "Leakage Blocking Status",
        ["check", "status", "severity", "blocking"],
        rows,
    )


def _make_console(*, stderr: bool) -> Any:
    if _rich_available() and Console is not None:
        return Console(stderr=stderr)

    class PlainConsole:
        def __init__(self, stream: Any) -> None:
            self.stream = stream

        def print(self, value: object) -> None:
            print(value, file=self.stream)

    return PlainConsole(sys.stderr if stderr else sys.stdout)


def _rich_available() -> bool:
    return Console is not None


def _request_header_fields(request: Any) -> dict[str, Any]:
    data = asdict(request) if is_dataclass(request) else dict(getattr(request, "__dict__", {}))
    keys = (
        "experiment_id",
        "branch",
        "role",
        "feature_group",
        "label_policy",
        "preprocessing_profile",
        "profile",
        "backend",
        "workers",
        "batch_rows",
        "reserved_ram_gb",
        "soft_ram_limit_gb",
        "hard_ram_limit_gb",
    )
    fields = {key: data.get(key) for key in keys if data.get(key) is not None}
    if "workers" in fields:
        fields["requested_workers"] = fields.pop("workers")
    return fields


def _default_summary(payload: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "status",
        "elapsed",
        "input_normalized_artifacts",
        "resume_skipped_count",
        "rows_read",
        "rows_written",
        "output_feature_artifacts",
        "throughput",
        "bottleneck",
        "report_paths",
        "stage_four_readiness_status",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            text_key = str(key)
            if any(secret in text_key.lower() for secret in SECRET_KEYS):
                sanitized[text_key] = "****"
            elif text_key.upper() == "DATABASE_URL":
                sanitized[text_key] = mask_database_url(str(item))
            else:
                sanitized[text_key] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def mask_database_url(value: str) -> str:
    if not value:
        return ""
    try:
        parts = urlsplit(value)
    except ValueError:
        return "****"
    if not parts.netloc:
        return "****"
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    username = parts.username or parts.scheme or "postgres"
    db = parts.path or ""
    return urlunsplit((parts.scheme, f"{username}:****@{host}{port}", db, "", ""))


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def _clean_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if value not in (None, "", [], {})}


def _int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _resource_snapshot() -> dict[str, float | None]:
    if psutil is None:
        return {}
    try:
        process = psutil.Process(os.getpid())
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "rss_gb": round(process.memory_info().rss / (1024**3), 3),
            "available_ram_gb": round(memory.available / (1024**3), 3),
        }
    except Exception:
        return {}


def _collect_paths(payload: dict[str, Any], key: str) -> dict[str, str]:
    value = payload.get(key)
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items() if isinstance(v, str)}
    return {}


def _collect_artifact_paths(payload: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"artifact_path", "feature_path", "normalized_snapshot_path"} and isinstance(value, str):
                paths.append(value)
            elif key == "parts" and isinstance(value, list):
                paths.extend(str(item) for item in value if isinstance(item, str))
            else:
                paths.extend(_collect_artifact_paths(value))
    elif isinstance(payload, list):
        for item in payload:
            paths.extend(_collect_artifact_paths(item))
    return sorted(dict.fromkeys(paths))


def _collect_blocking_issues(payload: dict[str, Any]) -> list[str]:
    issues = payload.get("blocking_issues")
    if isinstance(issues, list):
        return [str(item) for item in issues]
    checks = payload.get("checks")
    if isinstance(checks, list):
        return [
            f"{check.get('check_group')}.{check.get('check_name')}: {check.get('message')}"
            for check in checks
            if isinstance(check, dict) and check.get("status") == "FAIL" and check.get("blocking")
        ]
    return []


def _collect_warnings(payload: Any) -> list[str]:
    warnings: list[str] = []
    if isinstance(payload, dict):
        value = payload.get("warnings")
        if isinstance(value, list):
            warnings.extend(str(item) for item in value)
        for item in payload.values():
            warnings.extend(_collect_warnings(item))
    elif isinstance(payload, list):
        for item in payload:
            warnings.extend(_collect_warnings(item))
    return sorted(dict.fromkeys(warnings))


def _derive_severity(payload: dict[str, Any]) -> str:
    checks = payload.get("checks")
    if isinstance(checks, list):
        severities = [str(check.get("severity")) for check in checks if isinstance(check, dict)]
        if "CRITICAL" in severities:
            return "CRITICAL"
        if "ERROR" in severities:
            return "ERROR"
        if "WARNING" in severities:
            return "WARNING"
    status = str(payload.get("status") or "")
    if status in {"FAIL", "FAILED", "ERROR", "BLOCKED", "BLOCKED_BY_LEAKAGE", "BLOCKED_BY_QUALITY"}:
        return "CRITICAL"
    if status in {"WARN", "PARTIAL_SUCCESS"}:
        return "WARNING"
    return "INFO"
