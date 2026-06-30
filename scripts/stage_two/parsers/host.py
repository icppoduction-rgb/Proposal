"""Host normalization parsers for CSV, JSON-lines, logs, and traces."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import STAGE_TWO_DEFAULT_BATCH_SIZE, STAGE_TWO_MAX_RAW_PREVIEW_BYTES
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol, unlabeled
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult, collect_parser_batches
from scripts.stage_two.parsers.common import (
    classify_helper_file,
    merge_json_objects,
    parser_report_warning,
)
from scripts.stage_two.parsers.csv_utils import (
    compact_row,
    first_present,
    first_present_with_name,
    is_empty_csv_row,
    looks_like_header,
    row_from_fieldnames,
    row_from_header,
)
from scripts.stage_two.parsers.input_reader import UniversalInputReader
from scripts.stage_two.parsers.json_utils import compact_json_row, flatten_json_object, loads_json_record
from scripts.stage_two.parsers.logs import ParsedLogLine, _enrich_log_row, parse_host_log_line
from scripts.stage_two.parsers.metrics import HOST_METRIC_SOURCE_FORMATS, HostMetricbeatParser
from scripts.stage_two.parsers.netflow import HostNetflowParser
from scripts.stage_two.parsers.xml import HostXmlParser


HOST_ADFA_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "process_id",
    "path",
    "sys_call",
    "event_id",
    "attack_cat",
    "attack_subcat",
    "label",
)
HOST_SERVICE_FILE_NAMES: frozenset[str] = frozenset({"feature_descr.csv", "ground_truth.csv"})
HOST_VALIDATION_RUN_FIELDS: tuple[str, ...] = (
    "image_name",
    "scenario_name",
    "is_executing_exploit",
    "warmup_time",
    "recording_time",
    "exploit_start_time",
)
HOST_VALIDATION_CONTEXT_FIELDS: tuple[str, ...] = (
    "image_name",
    "scenario_name",
    "warmup_time",
    "recording_time",
    "exploit_start_time",
)
HOST_TEST_LABEL_FIELDS: frozenset[str] = frozenset(
    {
        "label_binary",
        "label",
        "labels",
        "target",
        "class",
        "is_attack",
        "is_malicious",
        "malicious",
        "attack",
        "attack_cat",
        "attack_category",
        "attack_subcat",
        "alert",
        "is_executing_exploit",
        "event.action",
        "event_type",
        "exploit",
        "ids_alert",
        "rule.alert",
    }
)

HOST_HEADER_FIELDS: frozenset[str] = frozenset(
    {
        *HOST_ADFA_COLUMNS,
        *HOST_VALIDATION_RUN_FIELDS,
        "timestamp",
        "datetime",
        "date",
        "time",
        "@timestamp",
        "process_id",
        "pro_id",
        "pid",
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
        "event_label",
        "host",
        "ip",
        "label",
        "name",
        "short",
        "feature no",
        "feature name",
        "time_label",
        "type",
        "metadata",
    }
)
HOST_DATE_FIELDS: tuple[str, ...] = ("date", "Date", "event_date")
HOST_TIME_FIELDS: tuple[str, ...] = ("time", "Time", "event_time")
HOST_TIMESTAMP_FIELDS: tuple[str, ...] = (
    "@timestamp",
    "timestamp",
    "datetime",
    "event.timestamp",
    "event.created",
    "event.ingested",
    "winlog.time_created",
    "System.TimeCreated.SystemTime",
)
HOST_PROCESS_ID_FIELDS: tuple[str, ...] = ("process_id", "pro_id", "process.pid", "pid")
HOST_PATH_FIELDS: tuple[str, ...] = ("path", "file.path", "process.executable", "process.path")
HOST_SYSCALL_FIELDS: tuple[str, ...] = ("sys_call", "syscall", "syscall_name")
HOST_EVENT_ID_FIELDS: tuple[str, ...] = ("event_id", "EventID", "event.code")
HOST_JSON_SOURCE_TYPES: frozenset[str] = frozenset(
    {"json_lines", "json_array", "json_object", "json_scalar", "log_json_line"}
)
TRACE_KEY_VALUE_PATTERN = re.compile(r"(?P<key>[A-Za-z_][\w.\-]*)=(?P<value>\"[^\"]*\"|'[^']*'|\S+)")
TRACE_CALL_PATTERN = re.compile(
    r"\b(?P<name>[A-Za-z_][\w.$:@/-]*)\s*\((?P<arguments>.*)\)\s*(?:=\s*(?P<return_value>\S.*))?$"
)
TRACE_ISO_TIMESTAMP_PREFIX_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T ][^\s]+)\s+(?P<body>.+)$"
)
TRACE_RELATIVE_TIMESTAMP_PREFIX_PATTERN = re.compile(r"^(?P<relative_timestamp>\d+\.\d+)\s+(?P<body>.+)$")
TRACE_NAME_PATTERN = re.compile(r"^[A-Za-z_][\w.$:@/-]*$")
TRACE_TOKEN_PATTERN = re.compile(r"\S+")
GHC_MODULE_OFFSET_TOKEN_PATTERN = re.compile(
    r"^(?P<module>[A-Za-z0-9_.-]+\.(?:dll|exe|sys))\+0x(?P<offset>[0-9A-Fa-f]+)$",
    re.IGNORECASE,
)
SYSTEMD_JOURNAL_MAGIC = b"LPKSHHRH"
SYSTEMD_JOURNAL_FIELD_PATTERN = re.compile(
    rb"(?P<key>[A-Z_][A-Z0-9_]{1,63})=(?P<value>[^\x00\r\n]{0,4096})"
)
SYSTEMD_JOURNAL_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+")
HOST_LOG_PREVIEW_CHARS = min(512, STAGE_TWO_MAX_RAW_PREVIEW_BYTES)


class HostCsvParser(BaseParser):
    """Schema-aware parser for Host CSV event and metadata tables."""

    parser_name = "host_csv_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse host CSV rows into normalized host events."""
        return collect_parser_batches(self.parse_batches(path, context))

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse host CSV rows as bounded batches."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        file_path = Path(path)
        helper_decision = classify_helper_file(file_path, source_format=context.source_format)
        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        error_samples: list[str] = []
        schema_counts: dict[str, int] = {}
        reader = UniversalInputReader(file_path)
        with reader.iter_lines(keepends=True, skip_empty=False) as lines:
            for index, row in enumerate(_iter_host_csv_rows(lines, context, file_path)):
                rows_read += 1
                schema = str(row.get("_csv_schema") or "host_csv")
                schema_counts[schema] = schema_counts.get(schema, 0) + 1
                try:
                    events.append(_host_csv_row_to_event(self, row, index, context))
                except Exception as exc:
                    rows_failed += 1
                    error_samples.append(_error_sample(row, exc))
                if len(events) >= batch_size:
                    result = ParserResult(
                        rows_read=rows_read,
                        rows_parsed=len(events),
                        rows_failed=rows_failed,
                        events=events,
                        error_samples=error_samples,
                    )
                    self.validate_result(result)
                    yield result
                    events = []
                    rows_read = 0
                    rows_failed = 0
                    error_samples = []

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if schema_counts:
            warnings.extend(f"csv_schema={schema}:{count}" for schema, count in sorted(schema_counts.items()))
        if helper_decision.is_helper:
            warnings.append(
                parser_report_warning(
                    status="SUCCESS" if events else "SKIPPED",
                    reason=helper_decision.reason or "helper file",
                    helper_type=helper_decision.helper_type,
                )
            )
        status_override = None
        status_reason = None
        if rows_read == 0 and rows_failed == 0 and not events:
            if helper_decision.is_helper:
                status_override = "SKIPPED"
                status_reason = helper_decision.reason or "helper file has no metadata rows"
            else:
                status_override = "EMPTY_FILE"
                status_reason = "host CSV file has no readable data rows"
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
            status_override=status_override,
            status_reason=status_reason,
        )
        self.validate_result(result)
        yield result


class HostJsonLinesParser(BaseParser):
    """Parser for host JSON, JSON-lines, and Metricbeat/Filebeat-like logs."""

    parser_name = "host_json_lines_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse JSON-lines, JSON arrays, and single JSON host telemetry objects."""
        return collect_parser_batches(self.parse_batches(path, context))

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse JSON-lines as bounded batches; fallback for JSON arrays/objects."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if _looks_like_materialized_json_document(path):
            yield from _chunk_materialized_result(
                self._parse_materialized_json(path, context),
                batch_size=batch_size,
            )
            return

        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        error_samples: list[str] = []
        reader = UniversalInputReader(path)
        with reader.iter_lines(keepends=True, skip_empty=False) as lines:
            for line_number, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                rows_read += 1
                try:
                    record = loads_json_record(line)
                except json.JSONDecodeError as exc:
                    rows_failed += 1
                    error_samples.append(f"json line {line_number}: {exc.msg}")
                    continue
                try:
                    events.append(
                        _host_json_record_to_event(
                            self,
                            record,
                            line_number - 1,
                            context,
                            source_type="json_lines",
                        )
                    )
                except Exception as exc:
                    row = flatten_json_object(record)
                    rows_failed += 1
                    error_samples.append(_error_sample(row, exc))
                if len(events) >= batch_size:
                    result = ParserResult(
                        rows_read=rows_read,
                        rows_parsed=len(events),
                        rows_failed=rows_failed,
                        events=events,
                        error_samples=error_samples,
                    )
                    self.validate_result(result)
                    yield result
                    events = []
                    rows_read = 0
                    rows_failed = 0
                    error_samples = []

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if reader_metadata.base64_detected:
            warnings.append("base64_detected=True")
        status_override = None
        status_reason = None
        if rows_read == 0 and rows_failed == 0 and not events:
            status_override = "EMPTY_FILE"
            status_reason = "host JSON file has no readable JSON records"
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
            status_override=status_override,
            status_reason=status_reason,
        )
        self.validate_result(result)
        yield result

    def _parse_materialized_json(self, path: str | Path, context: ParserContext) -> ParserResult:
        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        error_samples: list[str] = []
        reader = UniversalInputReader(path)
        content_parts: list[str] = []
        with reader.iter_lines(keepends=True, skip_empty=False) as lines:
            content_parts.extend(lines)
        content = "".join(content_parts)

        for index, record, source_type, error in _iter_host_json_records(content):
            rows_read += 1
            if error is not None:
                rows_failed += 1
                error_samples.append(error)
                continue
            try:
                events.append(_host_json_record_to_event(self, record, index, context, source_type=source_type))
            except Exception as exc:
                row = flatten_json_object(record)
                rows_failed += 1
                error_samples.append(_error_sample(row, exc))

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if reader_metadata.base64_detected:
            warnings.append("base64_detected=True")
        status_override = None
        status_reason = None
        if rows_read == 0 and rows_failed == 0 and not events:
            status_override = "EMPTY_FILE"
            status_reason = "host JSON file has no readable JSON records"
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
            status_override=status_override,
            status_reason=status_reason,
        )
        self.validate_result(result)
        return result


def _iter_host_json_records(content: str):
    stripped = content.strip()
    if not stripped:
        return

    try:
        payload = loads_json_record(stripped)
    except json.JSONDecodeError:
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                yield line_number - 1, loads_json_record(line), "json_lines", None
            except json.JSONDecodeError as exc:
                message = f"json line {line_number}: {exc.msg}"
                yield line_number - 1, {"line_number": line_number, "raw_line": line}, "json_lines", message
        return

    if isinstance(payload, list):
        for index, item in enumerate(payload):
            yield index, item, "json_array", None
        return
    if isinstance(payload, dict):
        yield 0, payload, "json_object", None
        return
    yield 0, payload, "json_scalar", None


def _looks_like_materialized_json_document(path: str | Path) -> bool:
    first_char: str | None = None
    second_char: str | None = None
    try:
        with Path(path).open("r", encoding="utf-8", errors="replace") as file:
            for line in file:
                stripped = line.lstrip()
                if not stripped:
                    continue
                if first_char is None:
                    first_char = stripped[0]
                    if first_char == "[":
                        return True
                    if first_char not in {"{"}:
                        return False
                    continue
                second_char = stripped[0]
                if second_char == "{":
                    return False
                if second_char in {'"', "}", "]"}:
                    return True
                return False
    except OSError:
        return False
    return first_char == "{"


def _chunk_materialized_result(result: ParserResult, *, batch_size: int) -> Iterator[ParserResult]:
    if not result.events:
        yield result
        return
    for start in range(0, len(result.events), batch_size):
        events = result.events[start : start + batch_size]
        batch = ParserResult(
            rows_read=result.rows_read if start == 0 else 0,
            rows_parsed=len(events),
            rows_failed=result.rows_failed if start == 0 else 0,
            events=events,
            warnings=result.warnings if start == 0 else [],
            bytes_read=result.bytes_read,
            files_read=result.files_read if start == 0 else 0,
            error_samples=result.error_samples if start == 0 else [],
            parse_errors_count=result.parse_errors_count if start == 0 else 0,
        )
        yield batch


def _host_json_record_to_event(
    parser: BaseParser,
    record: Any,
    index: int,
    context: ParserContext,
    *,
    source_type: str,
) -> dict[str, Any]:
    row = flatten_json_object(record)
    row["_json_source_type"] = source_type
    row["_json_record_index"] = index
    return _host_event_from_row(
        parser,
        row,
        index,
        context,
        modality=_host_json_modality(row),
    )


class HostLineLogParser(BaseParser):
    """Line-oriented parser for raw syslog/auth/log sources."""

    parser_name = "host_line_log_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse raw log lines into normalized host log events."""
        if context.source_format in HOST_METRIC_SOURCE_FORMATS:
            return HostMetricbeatParser(label_resolver=self.label_resolver).parse(path, context)
        return collect_parser_batches(self.parse_batches(path, context))

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse host log lines as bounded batches."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if context.source_format in HOST_METRIC_SOURCE_FORMATS:
            yield from HostMetricbeatParser(label_resolver=self.label_resolver).parse_batches(
                path,
                context,
                batch_size=batch_size,
            )
            return
        if _is_systemd_journal_file(path):
            yield from _parse_systemd_journal_batches(self, path, context, batch_size=batch_size)
            return

        helper_decision = classify_helper_file(path, source_format=context.source_format)
        if helper_decision.is_helper and not helper_decision.emit_metadata_event:
            reason = helper_decision.reason or "helper file"
            yield ParserResult(
                rows_read=0,
                rows_parsed=0,
                rows_failed=0,
                events=[],
                warnings=[
                    parser_report_warning(
                        status="SKIPPED",
                        reason=reason,
                        helper_type=helper_decision.helper_type,
                    )
                ],
                bytes_read=_file_size_or_none(path),
                status_override="SKIPPED",
                status_reason=reason,
            )
            return

        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        error_samples: list[str] = []
        reader = UniversalInputReader(path)
        with reader.iter_lines(keepends=False, skip_empty=False) as lines:
            for index, line in enumerate(lines):
                if not line.strip():
                    continue
                rows_read += 1
                parsed = parse_host_log_line(
                    line,
                    line_number=index + 1,
                    source_format=context.source_format,
                )
                if parsed.error is not None:
                    rows_failed += 1
                    error_samples.append(parsed.error)
                    continue
                try:
                    events.append(_host_line_record_to_event(self, parsed, index, context))
                except Exception as exc:
                    rows_failed += 1
                    error_samples.append(_error_sample(parsed.row, exc))
                if len(events) >= batch_size:
                    result = ParserResult(
                        rows_read=rows_read,
                        rows_parsed=len(events),
                        rows_failed=rows_failed,
                        events=events,
                        error_samples=error_samples,
                    )
                    self.validate_result(result)
                    yield result
                    events = []
                    rows_read = 0
                    rows_failed = 0
                    error_samples = []

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        status_override = None
        status_reason = None
        if rows_read == 0 and rows_failed == 0 and not events:
            status_override = "EMPTY_FILE"
            status_reason = "host line-log file has no readable log lines"
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
            status_override=status_override,
            status_reason=status_reason,
        )
        self.validate_result(result)
        yield result


def _host_line_record_to_event(
    parser: BaseParser,
    parsed: ParsedLogLine,
    index: int,
    context: ParserContext,
) -> dict[str, Any]:
    if parsed.json_payload is not None:
        row = flatten_json_object(parsed.json_payload)
        row.update(
            {
                key: value
                for key, value in parsed.row.items()
                if key.startswith("_") or key in {"line_number", "source_format", "event_index"}
            }
        )
        row["_json_source_type"] = "log_json_line"
        row["_json_record_index"] = index
        if not any(_pick(row, key) not in ("", None) for key in ("event_type", "event.action", "event.dataset")):
            row["event_type"] = "json_log"
        return _host_event_from_row(
            parser,
            row,
            index,
            context,
            modality=_host_json_modality(row),
        )
    return _host_event_from_row(
        parser,
        parsed.row,
        index,
        context,
        modality=_host_log_modality(parsed.row),
    )


def _parse_systemd_journal_batches(
    parser: BaseParser,
    path: str | Path,
    context: ParserContext,
    *,
    batch_size: int,
) -> Iterator[ParserResult]:
    events: list[dict[str, Any]] = []
    rows_read = 0
    rows_failed = 0
    error_samples: list[str] = []
    for row in _iter_systemd_journal_rows(path, source_format=context.source_format):
        rows_read += 1
        try:
            events.append(_host_event_from_row(parser, row, rows_read - 1, context, modality="journal"))
        except Exception as exc:
            rows_failed += 1
            error_samples.append(_error_sample(row, exc))
        if len(events) >= batch_size:
            result = ParserResult(
                rows_read=rows_read,
                rows_parsed=len(events),
                rows_failed=rows_failed,
                events=events,
                error_samples=error_samples,
            )
            parser.validate_result(result)
            yield result
            events = []
            rows_read = 0
            rows_failed = 0
            error_samples = []

    status_override = None
    status_reason = None
    if rows_read == 0 and rows_failed == 0 and not events:
        status_override = "FAILED"
        status_reason = "systemd journal file has no extractable MESSAGE fields"
    result = ParserResult(
        rows_read=rows_read,
        rows_parsed=len(events),
        rows_failed=rows_failed,
        events=events,
        warnings=["systemd_journal_binary_fallback=True"],
        bytes_read=_file_size_or_none(path),
        error_samples=error_samples,
        status_override=status_override,
        status_reason=status_reason,
    )
    parser.validate_result(result)
    yield result


def _iter_systemd_journal_rows(path: str | Path, *, source_format: str) -> Iterator[dict[str, Any]]:
    data = Path(path).read_bytes()
    current: dict[str, Any] = {}
    message_index = 0
    for match in SYSTEMD_JOURNAL_FIELD_PATTERN.finditer(data):
        key = match.group("key").decode("ascii", errors="ignore")
        value = _decode_systemd_journal_value(match.group("value"))
        if not key or value in ("", None):
            continue
        if key == "MESSAGE" and current.get("MESSAGE") not in ("", None):
            message_index += 1
            yield _systemd_journal_row(current, message_index, source_format=source_format)
            current = {}
        elif current.get("MESSAGE") not in ("", None) and key in current:
            message_index += 1
            yield _systemd_journal_row(current, message_index, source_format=source_format)
            current = {}
        current[key] = value
    if current.get("MESSAGE") not in ("", None):
        message_index += 1
        yield _systemd_journal_row(current, message_index, source_format=source_format)


def _systemd_journal_row(fields: dict[str, Any], index: int, *, source_format: str) -> dict[str, Any]:
    message = _string_or_none(fields.get("MESSAGE")) or ""
    timestamp = _systemd_journal_timestamp(fields)
    process_name = first_present(
        fields,
        ("SYSLOG_IDENTIFIER", "_COMM", "_EXE", "_SYSTEMD_UNIT", "UNIT", "USER_UNIT"),
    )
    row = {
        "_log_source_type": "systemd_journal_binary",
        "line_number": index,
        "event_index": index - 1,
        "source_format": source_format,
        "_raw_line_preview": message[:HOST_LOG_PREVIEW_CHARS],
        "_raw_line_sha256": hashlib.sha256(message.encode("utf-8", errors="replace")).hexdigest(),
        "_raw_line_length": len(message),
        "event_type": _systemd_journal_event_type(fields),
        "raw_event_name": process_name or "systemd_journal",
        "message": message[:HOST_LOG_PREVIEW_CHARS],
        "timestamp": timestamp,
        "host_name": fields.get("_HOSTNAME"),
        "process_name": process_name,
        "process_id": fields.get("_PID") or fields.get("SYSLOG_PID"),
        "user_name": fields.get("_UID"),
        "command_line": fields.get("_CMDLINE"),
        "file_path": fields.get("CODE_FILE") or fields.get("_EXE"),
        "journal_priority": fields.get("PRIORITY"),
        "journal_transport": fields.get("_TRANSPORT"),
        "journal_systemd_unit": fields.get("_SYSTEMD_UNIT") or fields.get("UNIT") or fields.get("USER_UNIT"),
        "journal_fields": dict(fields),
    }
    return _enrich_log_row(row)


def _systemd_journal_event_type(fields: dict[str, Any]) -> str:
    priority = _string_or_none(fields.get("PRIORITY"))
    if priority in {"0", "1", "2", "3"}:
        return "journal_error"
    if fields.get("SYSLOG_IDENTIFIER") == "kernel":
        return "journal_kernel"
    if fields.get("_SYSTEMD_UNIT") or fields.get("UNIT") or fields.get("USER_UNIT"):
        return "journal_unit"
    return "journal_message"


def _systemd_journal_timestamp(fields: dict[str, Any]) -> str | None:
    raw_value = _string_or_none(fields.get("_SOURCE_REALTIME_TIMESTAMP") or fields.get("__REALTIME_TIMESTAMP"))
    if raw_value is None or not raw_value.isdigit():
        return None
    try:
        return datetime.fromtimestamp(int(raw_value) / 1_000_000, tz=timezone.utc).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _decode_systemd_journal_value(value: bytes) -> str:
    text = value.decode("utf-8", errors="replace")
    text = SYSTEMD_JOURNAL_CONTROL_CHARS_PATTERN.sub(" ", text)
    return " ".join(text.split())


def _is_systemd_journal_file(path: str | Path) -> bool:
    try:
        with Path(path).open("rb") as stream:
            return stream.read(len(SYSTEMD_JOURNAL_MAGIC)) == SYSTEMD_JOURNAL_MAGIC
    except OSError:
        return False


class HostSyscallTraceParser(BaseParser):
    """Parser for syscall/API trace-like text streams."""

    parser_name = "host_syscall_trace_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse syscall trace lines and preserve event_order through event_index."""
        return collect_parser_batches(self.parse_batches(path, context))

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse syscall/API trace lines as bounded batches."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        helper_decision = classify_helper_file(path, source_format=context.source_format)
        if helper_decision.is_helper and not helper_decision.emit_metadata_event:
            reason = helper_decision.reason or "helper file"
            yield ParserResult(
                rows_read=0,
                rows_parsed=0,
                rows_failed=0,
                events=[],
                warnings=[
                    parser_report_warning(
                        status="SKIPPED",
                        reason=reason,
                        helper_type=helper_decision.helper_type,
                    )
                ],
                bytes_read=_file_size_or_none(path),
                status_override="SKIPPED",
                status_reason=reason,
            )
            return

        if _looks_like_txt_host_csv(path, source_format=context.source_format):
            yield from HostCsvParser(self.label_resolver).parse_batches(path, context, batch_size=batch_size)
            return

        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        event_index = 0
        error_samples: list[str] = []
        reader = UniversalInputReader(path)
        with reader.iter_lines(keepends=False, skip_empty=False) as lines:
            for line_index, line in enumerate(lines):
                if not line.strip():
                    continue
                ghc_rows = _iter_ghc_trace_sequence_rows(
                    line,
                    line_number=line_index + 1,
                    source_format=context.source_format,
                )
                sequence_rows = ghc_rows
                if sequence_rows is None:
                    sequence_rows = _iter_numeric_syscall_sequence_rows(
                        line,
                        line_number=line_index + 1,
                        source_format=context.source_format,
                    )
                if sequence_rows is None:
                    row, error = _parse_syscall_trace_line(
                        line,
                        line_number=line_index + 1,
                        source_format=context.source_format,
                    )
                    if error is not None:
                        rows_read += 1
                        rows_failed += 1
                        error_samples.append(error)
                        continue
                    rows: Iterator[dict[str, Any]] = iter((row,))
                else:
                    rows = sequence_rows
                for row in rows:
                    rows_read += 1
                    try:
                        events.append(_host_event_from_row(self, row, event_index, context, modality="syscall"))
                        event_index += 1
                    except Exception as exc:
                        rows_failed += 1
                        error_samples.append(_error_sample(row, exc))
                    if len(events) >= batch_size:
                        result = ParserResult(
                            rows_read=rows_read,
                            rows_parsed=len(events),
                            rows_failed=rows_failed,
                            events=events,
                            error_samples=error_samples,
                        )
                        self.validate_result(result)
                        yield result
                        events = []
                        rows_read = 0
                        rows_failed = 0
                        error_samples = []

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if reader_metadata.base64_detected:
            warnings.append("base64_detected=True")
        status_override = None
        status_reason = None
        if rows_read == 0 and rows_failed == 0 and not events:
            status_override = "EMPTY_FILE"
            status_reason = "host trace file has no readable trace lines"
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
            status_override=status_override,
            status_reason=status_reason,
        )
        self.validate_result(result)
        yield result


def _parse_syscall_trace_line(
    line: str,
    *,
    line_number: int,
    source_format: str,
) -> tuple[dict[str, Any], str | None]:
    text = line.strip()
    if _is_control_heavy_trace_line(text):
        return {}, f"line {line_number}: invalid control-heavy trace line"
    if not any(char.isalnum() for char in text):
        return {}, f"line {line_number}: trace line has no alphanumeric syscall/API token"

    body = text
    timestamp = None
    relative_timestamp = None
    timestamp_match = TRACE_ISO_TIMESTAMP_PREFIX_PATTERN.match(body)
    if timestamp_match:
        timestamp = timestamp_match.group("timestamp")
        body = timestamp_match.group("body").strip()
    else:
        relative_match = TRACE_RELATIVE_TIMESTAMP_PREFIX_PATTERN.match(body)
        if relative_match:
            relative_timestamp = relative_match.group("relative_timestamp")
            body = relative_match.group("body").strip()

    trace_fields = _trace_key_values(body)
    syscall_id, explicit_name = _syscall_id_and_name_from_fields(trace_fields)
    call_match = TRACE_CALL_PATTERN.search(body)
    arguments = _trace_first_field(trace_fields, ("arguments", "argument", "args", "arg", "argv"))
    return_value = _trace_first_field(trace_fields, ("return_value", "retval", "ret", "return", "result"))
    syscall_name = explicit_name
    if call_match:
        syscall_name = call_match.group("name")
        arguments = call_match.group("arguments") or arguments
        return_value = call_match.group("return_value") or return_value

    tokens = _trace_tokens(body)
    token_name, token_index = _trace_name_from_tokens(tokens, syscall_id=syscall_id)
    syscall_name = syscall_name or token_name
    if syscall_id is None:
        syscall_id = _trace_numeric_id_from_tokens(tokens)
    if syscall_name is None and syscall_id is not None:
        syscall_name = f"syscall_{syscall_id}"
    if syscall_name is None:
        return {}, f"line {line_number}: trace line has no syscall/API token"
    if arguments in ("", None) and token_index is not None:
        arguments = _trace_arguments_from_tokens(tokens, token_index)

    row: dict[str, Any] = {
        "_trace_source_type": "syscall_trace",
        "source_format": source_format,
        "line_number": line_number,
        "_raw_line_sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
        "_raw_line_length": len(text),
        "_raw_line_preview": _trace_line_preview(text),
        "raw_event_name": syscall_name,
        "syscall_name": syscall_name,
        "syscall_id": syscall_id,
        "event_id": syscall_id,
        "process_id": _trace_first_field(trace_fields, ("process_id", "pid", "process.pid", "tid")),
        "parent_process_id": _trace_first_field(trace_fields, ("parent_process_id", "ppid", "parent.pid")),
        "process_name": _trace_first_field(
            trace_fields,
            ("process_name", "process", "proc", "comm", "exe", "executable"),
        ),
        "user_name": _trace_first_field(trace_fields, ("user_name", "user", "uid", "euid")),
        "file_path": _trace_first_field(trace_fields, ("file_path", "file", "path", "pathname", "exe", "executable")),
        "arguments": arguments,
        "return_value": return_value,
        "relative_timestamp": relative_timestamp,
        "trace_fields": trace_fields,
        "trace_tokens": tokens,
        "command_line": _trace_line_preview(body),
    }
    if timestamp not in ("", None):
        row["timestamp"] = timestamp
    return row, None


def _iter_ghc_trace_sequence_rows(
    line: str,
    *,
    line_number: int,
    source_format: str,
) -> Iterator[dict[str, Any]] | None:
    if source_format.strip().lower() != "ghc":
        return None
    text = line.strip()
    if not text or _is_control_heavy_trace_line(text):
        return None

    sequence_length = 0
    for token in _iter_trace_tokens(text):
        cleaned = _clean_trace_token(token)
        match = GHC_MODULE_OFFSET_TOKEN_PATTERN.match(cleaned)
        if match is None:
            return None
        sequence_length += 1
    if sequence_length == 0:
        return None

    line_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    raw_line_length = len(text)
    raw_line_preview = _trace_line_preview(text)

    def rows() -> Iterator[dict[str, Any]]:
        for token_index, token in enumerate(_iter_trace_tokens(text)):
            cleaned = _clean_trace_token(token)
            match = GHC_MODULE_OFFSET_TOKEN_PATTERN.match(cleaned)
            if match is None:
                continue
            module_name = match.group("module")
            offset = f"0x{match.group('offset').lower()}"
            yield {
                "_trace_source_type": "ghc_module_offset_sequence",
                "source_format": source_format,
                "line_number": line_number,
                "token_index": token_index,
                "sequence_length": sequence_length,
                "_raw_line_sha256": line_hash,
                "_raw_line_length": raw_line_length,
                "_raw_line_preview": raw_line_preview,
                "raw_event_name": cleaned,
                "syscall_name": cleaned,
                "event_id": offset,
                "process_name": module_name,
                "module_name": module_name,
                "module_offset": offset,
                "command_line": cleaned,
            }

    return rows()


def _iter_numeric_syscall_sequence_rows(
    line: str,
    *,
    line_number: int,
    source_format: str,
) -> Iterator[dict[str, Any]] | None:
    if source_format.strip().lower() not in {"txt", "sc"}:
        return None
    text = line.strip()
    if not text or _is_control_heavy_trace_line(text):
        return None

    sequence_length = 0
    for token in _iter_trace_tokens(text):
        cleaned = _clean_trace_token(token)
        if not cleaned.isdigit():
            return None
        sequence_length += 1
    if sequence_length == 0:
        return None

    line_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    raw_line_length = len(text)
    raw_line_preview = _trace_line_preview(text)

    def rows() -> Iterator[dict[str, Any]]:
        for token_index, token in enumerate(_iter_trace_tokens(text)):
            syscall_id = _clean_trace_token(token)
            yield {
                "_trace_source_type": "numeric_syscall_sequence",
                "source_format": source_format,
                "line_number": line_number,
                "token_index": token_index,
                "sequence_length": sequence_length,
                "_raw_line_sha256": line_hash,
                "_raw_line_length": raw_line_length,
                "_raw_line_preview": raw_line_preview,
                "raw_event_name": f"syscall_{syscall_id}",
                "syscall_name": f"syscall_{syscall_id}",
                "syscall_id": syscall_id,
                "event_id": syscall_id,
                "command_line": syscall_id,
            }

    return rows()


def _trace_key_values(text: str) -> dict[str, str]:
    return {
        match.group("key"): _strip_trace_quotes(match.group("value"))
        for match in TRACE_KEY_VALUE_PATTERN.finditer(text)
    }


def _syscall_id_and_name_from_fields(fields: dict[str, str]) -> tuple[str | None, str | None]:
    syscall_value = _trace_first_field(
        fields,
        ("syscall_id", "syscall.id", "syscall", "syscall_number", "nr", "id"),
    )
    explicit_name = _trace_first_field(
        fields,
        ("syscall_name", "syscall.name", "api", "api_name", "call", "function", "function_name"),
    )
    syscall_id = None
    if syscall_value not in ("", None):
        if str(syscall_value).isdigit():
            syscall_id = str(syscall_value)
        elif explicit_name in ("", None):
            explicit_name = str(syscall_value)
    if explicit_name not in ("", None) and str(explicit_name).isdigit():
        syscall_id = syscall_id or str(explicit_name)
        explicit_name = None
    return syscall_id, explicit_name


def _trace_tokens(text: str) -> list[str]:
    return list(_iter_trace_tokens(text.strip()))


def _iter_trace_tokens(text: str) -> Iterator[str]:
    for match in TRACE_TOKEN_PATTERN.finditer(text):
        yield match.group(0)


def _trace_name_from_tokens(tokens: list[str], *, syscall_id: str | None) -> tuple[str | None, int | None]:
    for index, token in enumerate(tokens):
        cleaned = _clean_trace_token(token)
        if not cleaned or _looks_like_trace_key_value(token):
            continue
        if cleaned.isdigit():
            continue
        if syscall_id is not None and cleaned == syscall_id:
            continue
        if TRACE_NAME_PATTERN.match(cleaned):
            return cleaned, index
    return None, None


def _trace_numeric_id_from_tokens(tokens: list[str]) -> str | None:
    for token in tokens:
        if _looks_like_trace_key_value(token):
            continue
        cleaned = _clean_trace_token(token)
        if cleaned.isdigit():
            return cleaned
        if cleaned:
            return None
    return None


def _trace_arguments_from_tokens(tokens: list[str], name_index: int) -> str | None:
    arguments = [
        token
        for token in tokens[name_index + 1 :]
        if not _looks_like_trace_key_value(token)
    ]
    return " ".join(arguments) if arguments else None


def _trace_first_field(fields: dict[str, str], keys: tuple[str, ...]) -> str | None:
    lowered = {key.lower(): value for key, value in fields.items()}
    for key in keys:
        value = fields.get(key) or lowered.get(key.lower())
        if value not in ("", None):
            return value
    return None


def _clean_trace_token(token: str) -> str:
    return token.strip().strip(",;").split("(", 1)[0].strip()


def _looks_like_trace_key_value(token: str) -> bool:
    return "=" in token and TRACE_KEY_VALUE_PATTERN.match(token) is not None


def _strip_trace_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _is_control_heavy_trace_line(text: str) -> bool:
    if "\x00" in text:
        return True
    control_count = sum(1 for char in text if not char.isprintable() and char != "\t")
    return control_count / max(len(text), 1) > 0.2


def _trace_line_preview(text: str) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= STAGE_TWO_MAX_RAW_PREVIEW_BYTES:
        return text
    return encoded[:STAGE_TWO_MAX_RAW_PREVIEW_BYTES].decode("utf-8", errors="replace")


def _iter_host_csv_rows(lines: Any, context: ParserContext, file_path: Path):
    del context
    csv_reader = csv.reader(lines)
    first_values: list[str] | None = None
    for values in csv_reader:
        if is_empty_csv_row(values):
            continue
        first_values = values
        break
    if first_values is None:
        return

    file_name = file_path.name.lower()
    first_row_is_header = _first_row_is_header(first_values, file_name=file_name)
    if first_row_is_header:
        header = tuple(str(value or "").strip().lstrip("\ufeff") for value in first_values)
        schema = _schema_from_header(file_name, header)
        for values in csv_reader:
            if is_empty_csv_row(values):
                continue
            row = row_from_header(values, header)
            row["_csv_schema"] = _schema_from_row(file_name, row, default=schema)
            yield row
        return

    first_row = _headerless_host_row(first_values)
    yield first_row
    for values in csv_reader:
        if is_empty_csv_row(values):
            continue
        yield _headerless_host_row(values)


def _host_csv_row_to_event(
    parser: BaseParser,
    row: dict[str, Any],
    index: int,
    context: ParserContext,
) -> dict[str, Any]:
    schema = str(row.get("_csv_schema") or "host_csv")
    if schema == "feature_description":
        return _host_metadata_event(
            parser,
            row,
            index,
            context,
            event_type="host_csv_feature_description",
            reason="feature_descr.csv is a feature dictionary, not a host telemetry event",
            entity_id=_string_or_none(first_present(row, ("Feature Name", "feature_name", "name", "column"))),
        )
    if schema == "ground_truth":
        return _host_metadata_event(
            parser,
            row,
            index,
            context,
            event_type="host_csv_ground_truth",
            reason="ground_truth.csv is context metadata; no implicit label join is performed",
            entity_id=_ground_truth_entity_id(row),
        )
    if schema == "validation_runs":
        return _host_validation_run_event(parser, row, index, context)
    if schema == "label_metadata":
        return _host_metadata_event(
            parser,
            row,
            index,
            context,
            event_type="host_csv_label_metadata",
            reason="label-like CSV is preserved as metadata; no implicit TEST label join is performed",
            entity_id=_string_or_none(first_present(row, ("id", "record_id", "file", "file_name", "sample"))),
        )
    return _host_event_from_row(
        parser,
        row,
        index,
        context,
        modality="eventlog",
        require_host_signal=True,
    )


def _host_validation_run_event(
    parser: BaseParser,
    row: dict[str, Any],
    index: int,
    context: ParserContext,
) -> dict[str, Any]:
    scenario_name = _string_or_none(first_present(row, ("scenario_name", "scenario", "run_name")))
    image_name = _string_or_none(first_present(row, ("image_name", "image", "container_image")))
    entity_id = scenario_name or image_name
    label_fields = _resolve_host_labels(
        parser,
        row,
        context,
        label_source_override="scenario_metadata",
    )
    return parser.base_event(
        context,
        event_uid=_event_uid(context, index, entity_id),
        timestamp=None,
        timestamp_source=None,
        timestamp_type="event_order",
        event_index=index,
        entity_type="scenario",
        entity_id=entity_id,
        event_type="host_validation_run",
        raw_event_name=scenario_name,
        modality="host_metadata",
        raw_fields_json=compact_row(row),
        metadata_json=_host_csv_metadata(
            row,
            csv_file_role="scenario_metadata",
            reason="validation runs.csv-like scenario metadata",
            extra={
                "image_name": image_name,
                "scenario_name": scenario_name,
                "warmup_time": _float_or_none(first_present(row, ("warmup_time",))),
                "recording_time": _float_or_none(first_present(row, ("recording_time",))),
                "exploit_start_time": _float_or_none(first_present(row, ("exploit_start_time",))),
            },
        ),
        created_at=datetime.now(timezone.utc),
        **label_fields,
    )


def _host_metadata_event(
    parser: BaseParser,
    row: dict[str, Any],
    index: int,
    context: ParserContext,
    *,
    event_type: str,
    reason: str,
    entity_id: str | None,
) -> dict[str, Any]:
    return parser.base_event(
        context,
        event_uid=_event_uid(context, index, entity_id or event_type),
        timestamp=None,
        timestamp_source=None,
        timestamp_type="event_order",
        event_index=index,
        entity_type="metadata",
        entity_id=entity_id,
        event_type=event_type,
        raw_event_name=event_type,
        modality="host_metadata",
        raw_fields_json=compact_row(row),
        metadata_json=_host_csv_metadata(row, csv_file_role="service_file", reason=reason),
        created_at=datetime.now(timezone.utc),
        **unlabeled().as_event_fields(),
    )


def _host_event_from_row(
    parser: BaseParser,
    row: dict[str, Any],
    index: int,
    context: ParserContext,
    *,
    modality: str,
    require_host_signal: bool = False,
) -> dict[str, Any]:
    label_fields = _resolve_host_labels(parser, row, context)
    timestamp_source, timestamp = _timestamp_from_host_row(row)
    raw_event_name = _pick(row, "raw_event_name", "name", "message")
    event_type = (
        _pick(
            row,
            "event_type",
            "event.action",
            "event.dataset",
            "event.code",
            "winlog.event_id",
            "EventID",
            "event_id",
            "short",
            "event_label",
            "name",
            "syscall_name",
        )
        or modality
    )
    process_name = _pick(
        row,
        "process_name",
        "process.name",
        "process",
        "comm",
    )
    file_path = _pick(
        row,
        "file_path",
        "path",
        "file.path",
        "process.executable",
        "process.path",
        "log.file.path",
        "winlog.event_data.Image",
        "Image",
    )
    process_name = process_name or _process_name_from_path(file_path)
    syscall_name = _pick(row, "syscall_name", "sys_call", "syscall")
    host_name = _pick(
        row,
        "host_name",
        "host.name",
        "host.hostname",
        "host",
        "hostname",
        "agent.hostname",
        "winlog.computer_name",
        "Computer",
        "computer_name",
    )
    if require_host_signal and not _has_host_csv_signal(row):
        raise ValueError("row has no usable Host CSV telemetry fields")
    return parser.base_event(
        context,
        event_uid=_event_uid(context, index, event_type),
        timestamp=timestamp,
        timestamp_source=timestamp_source if timestamp else None,
        timestamp_type="absolute" if timestamp else "event_order",
        event_index=index,
        entity_type=_entity_type(modality),
        entity_id=process_name or host_name or syscall_name,
        event_type=_host_event_type(row, str(event_type), modality),
        raw_event_name=str(raw_event_name or event_type) if raw_event_name or event_type else None,
        modality=modality,
        host_name=host_name,
        user_name=_pick(
            row,
            "user_name",
            "user.name",
            "user",
            "uid",
            "winlog.event_data.User",
            "User",
            "SubjectUserName",
        ),
        process_id=_string_or_none(
            _pick(
                row,
                "process_id",
                "pro_id",
                "process.pid",
                "pid",
                "winlog.event_data.ProcessId",
                "ProcessId",
                "Event.System.Execution.ProcessID",
            )
        ),
        process_name=process_name,
        parent_process_id=_string_or_none(
            _pick(row, "parent_process_id", "process.parent.pid", "winlog.event_data.ParentProcessId")
        ),
        parent_process_name=_pick(row, "parent_process_name", "process.parent.name", "winlog.event_data.ParentImage"),
        src_ip=_pick(row, "src_ip", "source.ip", "source.address", "SourceAddress", "SourceIp", "IpAddress", "ip"),
        dst_ip=_pick(row, "dst_ip", "destination.ip", "destination.address", "DestinationAddress", "DestinationIp"),
        syscall_name=syscall_name,
        event_id=_string_or_none(
            _pick(row, "event_id", "EventID", "event.code", "winlog.event_id", "Event.System.EventID")
        ),
        command_line=_pick(row, "command_line", "process.command_line", "winlog.event_data.CommandLine", "CommandLine"),
        file_path=file_path,
        metric_name=_pick(row, "metric_name", "metricset.name"),
        metric_value=_float_or_none(_pick(row, "metric_value", "system.cpu.total.norm.pct")),
        raw_fields_json=_host_raw_fields(row),
        metadata_json=_host_metadata(row, modality=modality),
        created_at=datetime.now(timezone.utc),
        **label_fields,
    )


def _first_row_is_header(values: list[str], *, file_name: str) -> bool:
    if file_name in HOST_SERVICE_FILE_NAMES or file_name.startswith("runs"):
        return True
    return looks_like_header(values, HOST_HEADER_FIELDS)


def _schema_from_header(file_name: str, header: tuple[str, ...]) -> str:
    tokens = {value.strip().lower() for value in header if value.strip()}
    if file_name == "feature_descr.csv":
        return "feature_description"
    if file_name == "ground_truth.csv":
        return "ground_truth"
    if file_name.startswith("runs") or tokens.intersection({field.lower() for field in HOST_VALIDATION_CONTEXT_FIELDS}):
        return "validation_runs"
    if set(HOST_ADFA_COLUMNS).issubset(tokens):
        return "adfa_9_column"
    if _is_label_metadata_header(tokens):
        return "label_metadata"
    return "host_csv"


def _schema_from_row(file_name: str, row: dict[str, Any], *, default: str) -> str:
    if file_name == "feature_descr.csv":
        return "feature_description"
    if file_name == "ground_truth.csv":
        return "ground_truth"
    if _is_validation_run_row(row):
        return "validation_runs"
    if _is_adfa_row(row):
        return "adfa_9_column"
    if _is_label_metadata_row(row):
        return "label_metadata"
    return default


def _headerless_host_row(values: list[str]) -> dict[str, Any]:
    if len(values) == len(HOST_ADFA_COLUMNS):
        row = row_from_fieldnames(values, HOST_ADFA_COLUMNS)
        row["_csv_schema"] = "adfa_9_column"
        return row
    fieldnames = tuple(f"column_{index}" for index in range(1, len(values) + 1))
    row = row_from_fieldnames(values, fieldnames)
    row["_csv_schema"] = "host_csv_headerless"
    return row


def _is_validation_run_row(row: dict[str, Any]) -> bool:
    return any(first_present(row, (field,)) not in ("", None) for field in HOST_VALIDATION_CONTEXT_FIELDS)


def _is_adfa_row(row: dict[str, Any]) -> bool:
    return all(first_present(row, (field,)) not in ("", None) for field in ("date", "time", "path", "sys_call", "event_id"))


def _is_label_metadata_header(tokens: set[str]) -> bool:
    label_tokens = tokens.intersection(HOST_TEST_LABEL_FIELDS)
    host_tokens = tokens.intersection(
        {
            "date",
            "time",
            "timestamp",
            "process_id",
            "pro_id",
            "pid",
            "path",
            "sys_call",
            "syscall",
            "event_id",
            "image_name",
            "scenario_name",
        }
    )
    return bool(label_tokens) and not host_tokens


def _is_label_metadata_row(row: dict[str, Any]) -> bool:
    keys = {key.lower() for key in row if not key.startswith("_")}
    return _is_label_metadata_header(keys)


def _resolve_host_labels(
    parser: BaseParser,
    row: dict[str, Any],
    context: ParserContext,
    *,
    label_source_override: str | None = None,
) -> dict[str, Any]:
    label_row = _test_safe_label_row(row, context)
    label_fields = parser.label_resolver.resolve(label_row, context)  # type: ignore[attr-defined]
    if label_source_override and label_fields.get("label_source") == "embedded_column":
        label_fields = dict(label_fields)
        label_fields["label_source"] = label_source_override
    return label_fields


def _test_safe_label_row(row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
    if context.dataset_role != "TEST":
        return row
    return {
        key: value
        for key, value in row.items()
        if key.lower() not in HOST_TEST_LABEL_FIELDS
    }


def _timestamp_from_host_row(row: dict[str, Any]) -> tuple[str | None, datetime | None]:
    date_field, date_value = first_present_with_name(row, HOST_DATE_FIELDS)
    time_field, time_value = first_present_with_name(row, HOST_TIME_FIELDS)
    if date_value not in ("", None) and time_value not in ("", None):
        timestamp = _parse_timestamp(f"{date_value} {time_value}")
        if timestamp is not None:
            return f"{date_field}+{time_field}", timestamp
    if date_value in ("", None) and _looks_like_epoch_timestamp(time_value):
        timestamp = _parse_timestamp(time_value)
        if timestamp is not None:
            return time_field, timestamp

    timestamp_field, timestamp_value = first_present_with_name(row, HOST_TIMESTAMP_FIELDS)
    timestamp = _parse_timestamp(timestamp_value)
    return (timestamp_field if timestamp is not None else None), timestamp


def _has_host_csv_signal(row: dict[str, Any]) -> bool:
    if _is_label_metadata_row(row):
        return False
    return any(
        first_present(row, fields) not in ("", None)
        for fields in (
            HOST_PROCESS_ID_FIELDS,
            HOST_PATH_FIELDS,
            HOST_SYSCALL_FIELDS,
            HOST_EVENT_ID_FIELDS,
            HOST_TIMESTAMP_FIELDS,
            HOST_DATE_FIELDS,
            HOST_TIME_FIELDS,
        )
    )


def _host_event_type(row: dict[str, Any], selected_event_type: str, modality: str) -> str:
    schema = str(row.get("_csv_schema") or "")
    if schema == "adfa_9_column" or first_present(row, HOST_SYSCALL_FIELDS) not in ("", None):
        return "host_syscall"
    return selected_event_type if selected_event_type else modality


def _looks_like_txt_host_csv(path: str | Path, *, source_format: str) -> bool:
    if source_format.strip().lower() != "txt":
        return False
    try:
        with Path(path).open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
            sample = stream.readline(4096)
    except OSError:
        return False
    if not sample.strip() or "," not in sample:
        return False
    try:
        header = next(csv.reader([sample]))
    except csv.Error:
        return False
    tokens = {value.strip().lower() for value in header if value.strip()}
    return {"time", "name", "ip", "host"}.issubset(tokens)


def _host_csv_metadata(
    row: dict[str, Any],
    *,
    csv_file_role: str,
    reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    metadata: dict[str, Any] = {
        "csv_schema": row.get("_csv_schema"),
        "csv_file_role": csv_file_role,
        "parser_reason": reason,
    }
    if csv_file_role == "service_file":
        metadata["helper_file"] = True
        metadata["helper_action"] = "metadata_event_emitted"
    if first_present(row, ("attack_cat", "attack_category")) not in ("", None):
        metadata["attack_cat"] = first_present(row, ("attack_cat", "attack_category"))
    if first_present(row, ("attack_subcat",)) not in ("", None):
        metadata["attack_subcat"] = first_present(row, ("attack_subcat",))
    if extra:
        metadata.update(extra)
    return merge_json_objects(metadata, empty_as_none=True)


def _host_raw_fields(row: dict[str, Any]) -> dict[str, Any]:
    if "_json_source_type" in row:
        return compact_json_row(row)
    return compact_row(row)


def _host_metadata(row: dict[str, Any], *, modality: str) -> dict[str, Any] | None:
    if "_csv_schema" in row:
        return _host_csv_metadata(row, csv_file_role="telemetry")
    if "_log_source_type" in row:
        return _host_log_metadata(row, modality=modality)
    if "_trace_source_type" in row:
        return _host_trace_metadata(row, modality=modality)
    if str(row.get("_json_source_type") or "") in HOST_JSON_SOURCE_TYPES:
        return _host_json_metadata(row, modality=modality)
    return None


def _host_json_metadata(row: dict[str, Any], *, modality: str) -> dict[str, Any] | None:
    message = _pick(row, "message", "Message", "winlog.event_data.Message")
    metadata = {
        "json_source_type": row.get("_json_source_type"),
        "json_record_index": row.get("_json_record_index"),
        "modality": modality,
        "event_dataset": _pick(row, "event.dataset"),
        "event_module": _pick(row, "event.module"),
        "event_provider": _pick(row, "event.provider", "winlog.provider_name", "Provider.Name"),
        "log_file_path": _pick(row, "log.file.path"),
        "message_length": len(str(message)) if message not in ("", None) else None,
    }
    return merge_json_objects(metadata, empty_as_none=True)


def _host_json_modality(row: dict[str, Any]) -> str:
    dataset = str(_pick(row, "event.dataset", "event.module", "metricset.module") or "").lower()
    if any(token in dataset for token in ("system", "metric", "beat")):
        return "metric"
    if any(token in dataset for token in ("sysmon", "windows", "winlog")):
        return "eventlog"
    if _pick(row, "metricset.name", "system.cpu.total.norm.pct", "metric_name") not in ("", None):
        return "metric"
    return "eventlog"


def _host_log_metadata(row: dict[str, Any], *, modality: str) -> dict[str, Any] | None:
    metadata = {
        "log_source_type": row.get("_log_source_type"),
        "json_source_type": row.get("_json_source_type"),
        "line_number": row.get("line_number"),
        "source_format": row.get("source_format"),
        "raw_line_sha256": row.get("_raw_line_sha256"),
        "raw_line_length": row.get("_raw_line_length"),
        "raw_line_preview_truncated": _line_preview_truncated(row),
        "partial_timestamp": row.get("partial_timestamp"),
        "timestamp_parse_status": row.get("timestamp_parse_status"),
        "journal_monotonic_seconds": _float_or_none(row.get("journal_monotonic_seconds")),
        "auth_method": row.get("auth_method"),
        "apache_module": row.get("apache_module"),
        "apache_severity": row.get("apache_severity"),
        "thread_id": row.get("thread_id"),
        "mail_queue_id": row.get("mail_queue_id"),
        "mail_client": row.get("mail_client"),
        "mail_recipient": row.get("mail_recipient"),
        "modality": modality,
    }
    return merge_json_objects(metadata, empty_as_none=True)


def _host_log_modality(row: dict[str, Any]) -> str:
    event_type = str(row.get("event_type") or "").lower()
    source_format = str(row.get("source_format") or "").lower()
    process_name = str(row.get("process_name") or "").lower()
    if event_type.startswith("auth_") or source_format == "auth.log" or process_name in {"sshd", "sudo"}:
        return "auth"
    if event_type.startswith("mail_") or "mail" in source_format or "postfix" in process_name:
        return "mail"
    if "journal" in source_format or row.get("_log_source_type") == "journal":
        return "journal"
    return "log"


def _host_trace_metadata(row: dict[str, Any], *, modality: str) -> dict[str, Any] | None:
    arguments = row.get("arguments")
    metadata = {
        "trace_source_type": row.get("_trace_source_type"),
        "line_number": row.get("line_number"),
        "source_format": row.get("source_format"),
        "raw_line_sha256": row.get("_raw_line_sha256"),
        "raw_line_length": row.get("_raw_line_length"),
        "raw_line_preview_truncated": _line_preview_truncated(row),
        "syscall_id": row.get("syscall_id"),
        "module_name": row.get("module_name"),
        "module_offset": row.get("module_offset"),
        "token_index": row.get("token_index"),
        "sequence_length": row.get("sequence_length"),
        "arguments_length": len(str(arguments)) if arguments not in ("", None) else None,
        "return_value": row.get("return_value"),
        "relative_timestamp": row.get("relative_timestamp"),
        "modality": modality,
    }
    return merge_json_objects(metadata, empty_as_none=True)


def _line_preview_truncated(row: dict[str, Any]) -> bool | None:
    preview = row.get("_raw_line_preview")
    length = row.get("_raw_line_length")
    if preview is None or length is None:
        return None
    try:
        return int(length) > len(str(preview))
    except (TypeError, ValueError):
        return None


def _ground_truth_entity_id(row: dict[str, Any]) -> str | None:
    return _string_or_none(
        first_present(
            row,
            (
                "scenario_name",
                "scenario",
                "attack",
                "attack_cat",
                "src_ip",
                "dst_ip",
                "source_ip",
                "destination_ip",
            ),
        )
    )


def _process_name_from_path(value: Any) -> str | None:
    if value in ("", None):
        return None
    name = Path(str(value)).name
    return name or None


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
    text = str(value).strip()
    try:
        numeric_timestamp = float(text)
        while abs(numeric_timestamp) > 10_000_000_000:
            numeric_timestamp /= 1000
        return datetime.fromtimestamp(numeric_timestamp, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is not None:
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    for format_string in (
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%m-%d-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M",
    ):
        try:
            return datetime.strptime(text, format_string).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _looks_like_epoch_timestamp(value: Any) -> bool:
    if value in ("", None):
        return False
    text = str(value).strip()
    return bool(re.fullmatch(r"\d{9,16}(?:\.\d+)?", text))


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
    if modality == "host_metadata":
        return "metadata"
    return "host"


def _event_uid(context: ParserContext, index: int, event_type: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{event_type or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def _error_sample(row: dict[str, Any], exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}; row={compact_row(row)}"


def _file_size_or_none(path: str | Path) -> int | None:
    try:
        return Path(path).stat().st_size
    except OSError:
        return None
