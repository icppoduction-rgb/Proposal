"""Host normalization parsers for CSV, JSON-lines, logs, and traces."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol, unlabeled
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import merge_json_objects
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
from scripts.stage_two.parsers.json_utils import compact_json_row, flatten_json_object
from scripts.stage_two.parsers.logs import ParsedLogLine, parse_host_log_line
from scripts.stage_two.parsers.metrics import HOST_METRIC_SOURCE_FORMATS, HostMetricbeatParser


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
        "label",
        "feature no",
        "feature name",
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


class HostCsvParser(BaseParser):
    """Schema-aware parser for Host CSV event and metadata tables."""

    parser_name = "host_csv_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse host CSV rows into normalized host events."""
        file_path = Path(path)
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

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if schema_counts:
            warnings.extend(f"csv_schema={schema}:{count}" for schema, count in sorted(schema_counts.items()))
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
        )
        self.validate_result(result)
        return result


class HostJsonLinesParser(BaseParser):
    """Parser for host JSON, JSON-lines, and Metricbeat/Filebeat-like logs."""

    parser_name = "host_json_lines_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse JSON-lines, JSON arrays, and single JSON host telemetry objects."""
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
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
        )
        self.validate_result(result)
        return result


def _iter_host_json_records(content: str):
    stripped = content.strip()
    if not stripped:
        return

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                yield line_number - 1, json.loads(line), "json_lines", None
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

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
        )
        self.validate_result(result)
        return result


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


class HostSyscallTraceParser(BaseParser):
    """Parser for syscall/API trace-like text streams."""

    parser_name = "host_syscall_trace_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

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
    raw_event_name = _pick(row, "raw_event_name")
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
        src_ip=_pick(row, "src_ip", "source.ip", "source.address", "SourceAddress", "SourceIp", "IpAddress"),
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
        )
    )


def _host_event_type(row: dict[str, Any], selected_event_type: str, modality: str) -> str:
    schema = str(row.get("_csv_schema") or "")
    if schema == "adfa_9_column" or first_present(row, HOST_SYSCALL_FIELDS) not in ("", None):
        return "host_syscall"
    return selected_event_type if selected_event_type else modality


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
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except ValueError:
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
