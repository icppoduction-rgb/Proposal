"""Host normalization parsers for CSV, JSON-lines, logs, and traces."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.dns import LabelResolverProtocol, UnlabeledResolver


HOST_CSV_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "process_id",
    "process_name",
    "path",
    "sys_call",
    "event_id",
    "event_type",
    "label",
    "metadata",
)

HOST_HEADER_FIELDS: frozenset[str] = frozenset(
    {
        "timestamp",
        "time",
        "@timestamp",
        "process_id",
        "process.pid",
        "process_name",
        "process.name",
        "path",
        "file.path",
        "sys_call",
        "syscall",
        "syscall_name",
        "event_id",
        "event.code",
        "event_type",
        "event.action",
        "label",
        "metadata",
    }
)


class HostCsvParser(BaseParser):
    """Parser for host CSV event tables."""

    parser_name = "host_csv_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse host CSV rows into normalized host events."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        with Path(path).open("r", encoding="utf-8", errors="replace", newline="") as file:
            sample = file.read(4096)
            file.seek(0)
            reader = csv.DictReader(file) if _has_csv_header(sample) else csv.DictReader(file, fieldnames=HOST_CSV_COLUMNS)
            for index, row in enumerate(reader):
                try:
                    events.append(_host_event_from_row(self, row, index, context, modality="eventlog"))
                except Exception:
                    rows_failed += 1
        result = ParserResult(len(events) + rows_failed, len(events), rows_failed, events)
        self.validate_result(result)
        return result


class HostJsonLinesParser(BaseParser):
    """Parser for host JSON-lines and Metricbeat-like logs."""

    parser_name = "host_json_lines_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse JSON-lines host telemetry into normalized host events."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        with Path(path).open("r", encoding="utf-8", errors="replace") as file:
            for index, line in enumerate(file):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    events.append(_host_event_from_row(self, row, index, context, modality="metric"))
                except Exception:
                    rows_failed += 1
        result = ParserResult(len(events) + rows_failed, len(events), rows_failed, events)
        self.validate_result(result)
        return result


class HostLineLogParser(BaseParser):
    """Line-oriented parser for raw syslog/auth/log sources."""

    parser_name = "host_line_log_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse raw log lines into normalized host log events."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        with Path(path).open("r", encoding="utf-8", errors="replace") as file:
            for index, line in enumerate(file):
                message = line.rstrip("\n")
                if not message:
                    continue
                try:
                    row = {"message": message}
                    events.append(_host_event_from_row(self, row, index, context, modality="auth"))
                except Exception:
                    rows_failed += 1
        result = ParserResult(len(events) + rows_failed, len(events), rows_failed, events)
        self.validate_result(result)
        return result


class HostSyscallTraceParser(BaseParser):
    """Parser for syscall/API trace-like text streams."""

    parser_name = "host_syscall_trace_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse syscall trace lines and preserve event_order through event_index."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        with Path(path).open("r", encoding="utf-8", errors="replace") as file:
            for index, line in enumerate(file):
                syscall = line.strip()
                if not syscall:
                    continue
                try:
                    row = {"syscall_name": syscall}
                    events.append(_host_event_from_row(self, row, index, context, modality="syscall"))
                except Exception:
                    rows_failed += 1
        result = ParserResult(len(events) + rows_failed, len(events), rows_failed, events)
        self.validate_result(result)
        return result


def _host_event_from_row(
    parser: BaseParser,
    row: dict[str, Any],
    index: int,
    context: ParserContext,
    *,
    modality: str,
) -> dict[str, Any]:
    label_fields = parser.label_resolver.resolve(row, context)  # type: ignore[attr-defined]
    timestamp = _parse_timestamp(_pick(row, "@timestamp", "timestamp", "time"))
    event_type = _pick(row, "event_type", "event.action", "event_id", "syscall_name") or modality
    process_name = _pick(row, "process_name", "process.name", "process", "comm")
    syscall_name = _pick(row, "syscall_name", "sys_call", "syscall")
    host_name = _pick(row, "host.name", "host", "hostname", "agent.hostname")
    return parser.base_event(
        context,
        event_uid=_event_uid(context, index, event_type),
        timestamp=timestamp,
        timestamp_source="source_column" if timestamp else None,
        timestamp_type="absolute" if timestamp else "event_order",
        event_index=index,
        entity_type=_entity_type(modality),
        entity_id=process_name or host_name or syscall_name,
        event_type=str(event_type),
        raw_event_name=str(event_type) if event_type else None,
        modality=modality,
        host_name=host_name,
        user_name=_pick(row, "user_name", "user.name", "user", "uid"),
        process_id=_string_or_none(_pick(row, "process_id", "process.pid", "pid")),
        process_name=process_name,
        parent_process_id=_string_or_none(_pick(row, "parent_process_id", "process.parent.pid")),
        parent_process_name=_pick(row, "parent_process_name", "process.parent.name"),
        src_ip=_pick(row, "src_ip", "source.ip", "SourceAddress"),
        dst_ip=_pick(row, "dst_ip", "destination.ip", "DestinationAddress"),
        syscall_name=syscall_name,
        event_id=_string_or_none(_pick(row, "event_id", "EventID", "event.code")),
        command_line=_pick(row, "command_line", "process.command_line"),
        file_path=_pick(row, "file_path", "path", "file.path"),
        metric_name=_pick(row, "metric_name", "metricset.name"),
        metric_value=_float_or_none(_pick(row, "metric_value", "system.cpu.total.norm.pct")),
        raw_fields_json={key: value for key, value in row.items() if value not in ("", None)},
        created_at=datetime.now(timezone.utc),
        **label_fields,
    )


def _has_csv_header(sample: str) -> bool:
    first_line = sample.splitlines()[0] if sample.splitlines() else ""
    if not first_line:
        return False
    tokens = {token.strip().lower() for token in next(csv.reader([first_line]))}
    return bool(tokens & HOST_HEADER_FIELDS)


def _pick(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = _nested_get(row, key)
        if value not in ("", None):
            return value
    return None


def _nested_get(row: dict[str, Any], dotted_key: str) -> Any:
    current: Any = row
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return row.get(dotted_key)
        current = current[part]
    return current


def _parse_timestamp(value: Any) -> datetime | None:
    if value in ("", None):
        return None
    text = str(value)
    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _float_or_none(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return None if value in ("", None) else str(value)


def _entity_type(modality: str) -> str:
    if modality == "syscall":
        return "syscall"
    if modality == "metric":
        return "metric"
    return "host"


def _event_uid(context: ParserContext, index: int, event_type: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{event_type or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()
