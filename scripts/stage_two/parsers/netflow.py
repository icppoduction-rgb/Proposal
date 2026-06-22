"""Host NetFlow, IDS flow, and WLS event log parsers."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import STAGE_TWO_DEFAULT_BATCH_SIZE, STAGE_TWO_MAX_RAW_PREVIEW_BYTES
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult, collect_parser_batches
from scripts.stage_two.parsers.common import merge_json_objects
from scripts.stage_two.parsers.csv_utils import (
    compact_row,
    is_empty_csv_row,
    looks_like_header,
    row_from_fieldnames,
    row_from_header,
)
from scripts.stage_two.parsers.input_reader import UniversalInputReader
from scripts.stage_two.parsers.json_utils import compact_json_row, flatten_json_object


HOST_NETFLOW_SOURCE_FORMATS: frozenset[str] = frozenset(
    {"netflow_day", "netflow_ids", "wls_day"}
)
NETFLOW_DAY_COLUMNS: tuple[str, ...] = (
    "time",
    "duration",
    "src_host",
    "dst_host",
    "protocol",
    "src_port",
    "dst_port",
    "src_packets",
    "dst_packets",
    "src_bytes",
    "dst_bytes",
)
GENERIC_FLOW_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "bytes",
    "packets",
    "duration",
    "direction",
)
NETFLOW_HEADER_FIELDS: frozenset[str] = frozenset(
    {
        *NETFLOW_DAY_COLUMNS,
        *GENERIC_FLOW_COLUMNS,
        "source.ip",
        "destination.ip",
        "source.port",
        "destination.port",
        "dest_ip",
        "dest_port",
        "proto",
        "event_type",
        "alert.category",
        "alert.signature",
        "alert.severity",
        "flow_id",
        "EventID",
        "EventId",
        "event_id",
        "LogHost",
        "Source",
        "UserName",
        "DomainName",
        "LogonID",
        "Time",
    }
)
ABSOLUTE_TIMESTAMP_FIELDS: tuple[str, ...] = (
    "@timestamp",
    "timestamp",
    "event.timestamp",
    "event.created",
    "datetime",
    "date_time",
    "window_start",
    "window_date",
    "start_time",
    "end_time",
)
RELATIVE_TIMESTAMP_FIELDS: tuple[str, ...] = (
    "time",
    "Time",
    "relative_time",
    "relative_timestamp",
    "elapsed",
    "flow.start",
    "flow.end",
)
DATE_FIELDS: tuple[str, ...] = ("date", "Date", "event_date")
TIME_FIELDS: tuple[str, ...] = ("clock_time", "event_time", "time_of_day")
TEST_LABEL_FIELDS: frozenset[str] = frozenset(
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
        "is_executing_exploit",
        "exploit",
        "event_type",
        "event.action",
        "alert",
        "ids_alert",
        "rule.alert",
    }
)
DELIMITERS: tuple[str, ...] = (",", "\t", ";", "|")
NUMERIC_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
WINDOW_DATE_RE = re.compile(r"^\d{8}$")


@dataclass(frozen=True)
class ParsedNetflowLine:
    """One parsed text line or parser control result."""

    row: dict[str, Any] | None
    header: tuple[str, ...] | None
    error: str | None
    source_type: str


class HostNetflowParser(BaseParser):
    """Parser for Host netflow_day, netflow_ids, and wls_day sources."""

    parser_name = "host_netflow_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver(enable_filename_heuristics=False)

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse flow/eventlog text streams into normalized host network events."""
        return collect_parser_batches(self.parse_batches(path, context))

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse flow/eventlog text streams as bounded batches."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if context.source_format not in HOST_NETFLOW_SOURCE_FORMATS:
            yield ParserResult(
                rows_read=0,
                rows_parsed=0,
                rows_failed=1,
                events=[],
                warnings=[f"unsupported source_format for HostNetflowParser: {context.source_format}"],
                error_samples=[f"unsupported source_format: {context.source_format}"],
            )
            return

        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        header_rows = 0
        comment_rows = 0
        error_samples: list[str] = []
        header: tuple[str, ...] | None = None
        reader = UniversalInputReader(path)

        with reader.iter_lines(keepends=False, skip_empty=False) as lines:
            for line_number, line in enumerate(lines, start=1):
                text = line.strip()
                if not text:
                    continue
                if text.startswith("#"):
                    comment_rows += 1
                    continue

                parsed = _parse_netflow_line(text, context, header=header)
                if parsed.header is not None:
                    header = parsed.header
                    header_rows += 1
                    continue

                rows_read += 1
                if parsed.error is not None or parsed.row is None:
                    rows_failed += 1
                    error_samples.append(parsed.error or f"line {line_number}: row parse failed")
                    continue

                row = dict(parsed.row)
                row["_line_number"] = line_number
                row["_record_source_type"] = parsed.source_type
                row["_raw_line_sha256"] = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
                row["_raw_line_length"] = len(text)
                row["_raw_line_preview"] = _raw_preview(text)
                try:
                    events.append(
                        _netflow_row_to_event(
                            self,
                            row,
                            event_index=len(events),
                            context=context,
                        )
                    )
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
        if reader_metadata.compression_hint:
            warnings.append(f"compression_hint={reader_metadata.compression_hint}")
        if header_rows:
            warnings.append(f"header_rows_skipped={header_rows}")
        if comment_rows:
            warnings.append(f"comment_rows_skipped={comment_rows}")

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
        yield result


def _parse_netflow_line(
    text: str,
    context: ParserContext,
    *,
    header: tuple[str, ...] | None,
) -> ParsedNetflowLine:
    if text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            return ParsedNetflowLine(None, None, f"json line: {exc.msg}", "json_line")
        if not isinstance(payload, dict):
            return ParsedNetflowLine(None, None, "json line: expected JSON object", "json_line")
        row = flatten_json_object(payload)
        row["_netflow_schema"] = f"{context.source_format}_json_line"
        return ParsedNetflowLine(row, None, None, "json_line")

    values = _split_text_record(text)
    if is_empty_csv_row(values):
        return ParsedNetflowLine(None, None, None, "empty_line")
    if header is None and _looks_like_netflow_header(values):
        return ParsedNetflowLine(None, tuple(_normalize_header(values)), None, "header")

    if header is not None:
        row = row_from_header(values, header)
        row["_netflow_schema"] = f"{context.source_format}_headered"
        return ParsedNetflowLine(row, None, None, "delimited_headered")

    if context.source_format == "netflow_day" and len(values) >= len(NETFLOW_DAY_COLUMNS):
        row = row_from_fieldnames(values, NETFLOW_DAY_COLUMNS)
        row["_netflow_schema"] = "netflow_day_11_column"
        return ParsedNetflowLine(row, None, None, "delimited_headerless")

    if len(values) >= 5:
        fieldnames = GENERIC_FLOW_COLUMNS[: min(len(values), len(GENERIC_FLOW_COLUMNS))]
        row = row_from_fieldnames(values, fieldnames)
        row["_netflow_schema"] = f"{context.source_format}_generic_positional"
        return ParsedNetflowLine(row, None, None, "delimited_headerless")

    return ParsedNetflowLine(None, None, f"not enough fields for {context.source_format}: {values!r}", "unknown")


def _netflow_row_to_event(
    parser: BaseParser,
    row: dict[str, Any],
    *,
    event_index: int,
    context: ParserContext,
) -> dict[str, Any]:
    timestamp_source, timestamp, timestamp_type, relative_time = _timestamp_from_row(row)
    src_ip = _string_or_none(
        _pick(
            row,
            "src_ip",
            "source.ip",
            "source_ip",
            "src_host",
            "src",
            "SourceAddress",
            "SourceIp",
        )
    )
    dst_ip = _string_or_none(
        _pick(
            row,
            "dst_ip",
            "dest_ip",
            "destination.ip",
            "destination_ip",
            "dst_host",
            "dst",
            "DestinationAddress",
            "DestinationIp",
        )
    )
    src_port = _int_or_none(_pick(row, "src_port", "source.port", "sport", "srcport", "SourcePort"))
    dst_port = _int_or_none(
        _pick(row, "dst_port", "dest_port", "destination.port", "dport", "dstport", "DestinationPort")
    )
    protocol = _protocol(row)
    bytes_total = _sum_first_available(
        row,
        ("bytes", "flow.bytes", "flow.bytes_toserver", "flow.bytes_toclient"),
        (("src_bytes", "dst_bytes"), ("bytes_toserver", "bytes_toclient")),
    )
    packets_total = _sum_first_available(
        row,
        ("packets", "pkts", "flow.pkts", "flow.pkts_toserver", "flow.pkts_toclient"),
        (("src_packets", "dst_packets"), ("pkts_toserver", "pkts_toclient")),
    )
    duration = _float_or_none(_pick(row, "duration", "flow.duration", "elapsed", "dur"))
    direction = _string_or_none(_pick(row, "direction", "flow.direction", "dir"))
    modality = _modality(row, context)
    event_type = _event_type(row, context, modality)
    raw_event_name = _raw_event_name(row, event_type)
    host_name = _string_or_none(
        _pick(row, "host.name", "host", "hostname", "LogHost", "loghost", "Computer", "computer_name")
    )
    user_name = _string_or_none(_pick(row, "user.name", "UserName", "username", "user", "SubjectUserName"))
    event_id = _string_or_none(_pick(row, "event_id", "EventID", "EventId", "event.code", "winlog.event_id"))
    entity_id = _entity_id(
        modality=modality,
        src_ip=src_ip,
        dst_ip=dst_ip,
        host_name=host_name,
        event_id=event_id,
        raw_event_name=raw_event_name,
    )
    label_fields = _resolve_netflow_labels(parser, row, context)

    return parser.base_event(
        context,
        event_uid=_event_uid(context, event_index, entity_id or event_type),
        timestamp=timestamp,
        timestamp_source=timestamp_source if timestamp else None,
        timestamp_type=timestamp_type,
        event_index=event_index,
        entity_type=_entity_type(modality),
        entity_id=entity_id,
        event_type=event_type,
        raw_event_name=raw_event_name,
        modality=modality,
        host_name=host_name,
        user_name=user_name,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        event_id=event_id,
        process_id=_string_or_none(_pick(row, "process_id", "ProcessId", "process.pid", "PID")),
        process_name=_string_or_none(_pick(row, "process_name", "ProcessName", "process.name", "Image")),
        parent_process_id=_string_or_none(_pick(row, "parent_process_id", "ParentProcessId", "process.parent.pid")),
        parent_process_name=_string_or_none(_pick(row, "parent_process_name", "ParentProcessName")),
        command_line=_string_or_none(_pick(row, "command_line", "CommandLine", "process.command_line")),
        file_path=_string_or_none(_pick(row, "file_path", "path", "TargetFilename", "Image", "module_path")),
        raw_fields_json=compact_json_row(row),
        features_json=_flow_features(
            bytes_total=bytes_total,
            packets_total=packets_total,
            duration=duration,
            direction=direction,
            protocol=protocol,
        ),
        metadata_json=_metadata(
            row,
            context,
            modality=modality,
            event_type=event_type,
            relative_time=relative_time,
            bytes_total=bytes_total,
            packets_total=packets_total,
            duration=duration,
            direction=direction,
        ),
        created_at=datetime.now(timezone.utc),
        **label_fields,
    )


def _split_text_record(text: str) -> list[str]:
    delimiter = _detect_delimiter(text)
    if delimiter is None:
        return [value for value in re.split(r"\s+", text.strip()) if value != ""]
    return [value.strip() for value in next(csv.reader([text], delimiter=delimiter))]


def _detect_delimiter(text: str) -> str | None:
    counts = {delimiter: text.count(delimiter) for delimiter in DELIMITERS}
    delimiter, count = max(counts.items(), key=lambda item: item[1])
    return delimiter if count > 0 else None


def _looks_like_netflow_header(values: list[str]) -> bool:
    normalized = [value.strip().lstrip("\ufeff") for value in values]
    return looks_like_header(normalized, {field.lower() for field in NETFLOW_HEADER_FIELDS})


def _normalize_header(values: list[str]) -> list[str]:
    return [value.strip().lstrip("\ufeff") or f"column_{index}" for index, value in enumerate(values, start=1)]


def _timestamp_from_row(row: dict[str, Any]) -> tuple[str | None, datetime | None, str, Any]:
    date_field, date_value = _first_present_with_name(row, DATE_FIELDS)
    time_field, time_value = _first_present_with_name(row, TIME_FIELDS)
    if date_value not in ("", None) and time_value not in ("", None):
        timestamp = _parse_absolute_timestamp(f"{date_value} {time_value}", allow_numeric_epoch=False)
        if timestamp is not None:
            return f"{date_field}+{time_field}", timestamp, "absolute", None

    for field in ABSOLUTE_TIMESTAMP_FIELDS:
        source_name, value = _first_present_with_name(row, (field,))
        timestamp = _parse_absolute_timestamp(value, allow_numeric_epoch=True)
        if timestamp is not None:
            return source_name, timestamp, "absolute", None
        if value not in ("", None) and _looks_like_relative_number(value):
            return source_name, None, "relative", _float_or_text(value)

    for field in RELATIVE_TIMESTAMP_FIELDS:
        source_name, value = _first_present_with_name(row, (field,))
        timestamp = _parse_absolute_timestamp(value, allow_numeric_epoch=False)
        if timestamp is not None:
            return source_name, timestamp, "absolute", None
        if value not in ("", None):
            return source_name, None, "relative", _float_or_text(value)

    return None, None, "event_order", None


def _parse_absolute_timestamp(value: Any, *, allow_numeric_epoch: bool) -> datetime | None:
    if value in ("", None):
        return None
    text = str(value).strip()
    if not text:
        return None
    if WINDOW_DATE_RE.match(text):
        try:
            return datetime.strptime(text, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if allow_numeric_epoch and NUMERIC_RE.match(text):
        number = float(text)
        if number > 10_000_000_000:
            number = number / 1000.0
        if number >= 946_684_800:
            try:
                return datetime.fromtimestamp(number, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is not None:
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    for format_string in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%m-%d-%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, format_string).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _protocol(row: dict[str, Any]) -> str | None:
    value = _pick(row, "protocol", "proto", "app_proto", "transport", "Protocol")
    if value in ("", None):
        return None
    text = str(value).strip()
    if text == "6":
        return "TCP"
    if text == "17":
        return "UDP"
    if text == "1":
        return "ICMP"
    return text.upper() if text.lower() in {"tcp", "udp", "icmp"} else text


def _modality(row: dict[str, Any], context: ParserContext) -> str:
    if context.source_format == "wls_day" and _has_wls_eventlog_signal(row):
        return "host_eventlog"
    if context.source_format == "netflow_ids":
        if _has_flow_signal(row) or _has_ids_signal(row):
            return "host_network_flow"
        return "host_eventlog"
    if context.source_format == "wls_day":
        return "host_eventlog" if _has_wls_eventlog_signal(row) else "host_network_flow"
    return "network_flow"


def _event_type(row: dict[str, Any], context: ParserContext, modality: str) -> str:
    event_type = _pick(row, "event_type", "event.action", "event.dataset")
    event_id = _string_or_none(_pick(row, "EventID", "EventId", "event_id", "event.code"))
    if context.source_format == "wls_day" or modality == "host_eventlog":
        return f"windows_event_{event_id}" if event_id else "host_eventlog"
    if _has_ids_signal(row) or str(event_type or "").lower() == "alert":
        return "ids_alert"
    if event_type not in ("", None) and str(event_type).lower() not in {"flow", "netflow"}:
        return str(event_type)
    return "network_flow"


def _raw_event_name(row: dict[str, Any], event_type: str) -> str | None:
    return _string_or_none(
        _pick(
            row,
            "alert.signature",
            "signature",
            "rule.name",
            "raw_event_name",
            "event.action",
            "event.dataset",
            "Source",
            "Provider.Name",
            "EventID",
            "event_id",
        )
        or event_type
    )


def _has_flow_signal(row: dict[str, Any]) -> bool:
    return any(
        _pick(row, key) not in ("", None)
        for key in (
            "src_ip",
            "dst_ip",
            "source.ip",
            "destination.ip",
            "src_host",
            "dst_host",
            "src_port",
            "dst_port",
            "flow_id",
            "flow.bytes_toserver",
            "flow.pkts_toserver",
        )
    )


def _has_ids_signal(row: dict[str, Any]) -> bool:
    return any(
        _pick(row, key) not in ("", None)
        for key in (
            "alert.category",
            "alert.signature",
            "alert.severity",
            "rule.alert",
            "ids_alert",
        )
    )


def _has_wls_eventlog_signal(row: dict[str, Any]) -> bool:
    return any(
        _pick(row, key) not in ("", None)
        for key in ("EventID", "EventId", "event_id", "LogHost", "Source", "UserName", "LogonID")
    )


def _entity_id(
    *,
    modality: str,
    src_ip: str | None,
    dst_ip: str | None,
    host_name: str | None,
    event_id: str | None,
    raw_event_name: str | None,
) -> str | None:
    if modality in {"network_flow", "host_network_flow"}:
        if src_ip and dst_ip:
            return f"{src_ip}->{dst_ip}"
        return src_ip or dst_ip
    if host_name and event_id:
        return f"{host_name}:{event_id}"
    return host_name or raw_event_name or event_id


def _entity_type(modality: str) -> str:
    if modality in {"network_flow", "host_network_flow"}:
        return "network_flow"
    return "host"


def _flow_features(
    *,
    bytes_total: float | None,
    packets_total: float | None,
    duration: float | None,
    direction: str | None,
    protocol: str | None,
) -> dict[str, Any] | None:
    return merge_json_objects(
        {
            "bytes": bytes_total,
            "packets": packets_total,
            "duration": duration,
            "direction": direction,
            "protocol": protocol,
        },
        empty_as_none=True,
    )


def _metadata(
    row: dict[str, Any],
    context: ParserContext,
    *,
    modality: str,
    event_type: str,
    relative_time: Any,
    bytes_total: float | None,
    packets_total: float | None,
    duration: float | None,
    direction: str | None,
) -> dict[str, Any] | None:
    metadata = {
        "source_format": context.source_format,
        "netflow_schema": row.get("_netflow_schema"),
        "record_source_type": row.get("_record_source_type"),
        "line_number": row.get("_line_number"),
        "raw_line_sha256": row.get("_raw_line_sha256"),
        "raw_line_length": row.get("_raw_line_length"),
        "raw_line_preview_truncated": _line_preview_truncated(row),
        "modality": modality,
        "event_type": event_type,
        "relative_time": relative_time,
        "flow_id": _pick(row, "flow_id", "flow.id"),
        "bytes": bytes_total,
        "packets": packets_total,
        "duration": duration,
        "direction": direction,
        "alert_category": _pick(row, "alert.category", "category"),
        "alert_signature": _pick(row, "alert.signature", "signature"),
        "alert_severity": _pick(row, "alert.severity", "severity"),
        "ids_event_type": _pick(row, "event_type"),
        "loghost": _pick(row, "LogHost", "loghost"),
        "source": _pick(row, "Source", "source"),
        "domain_name": _pick(row, "DomainName", "domain"),
        "logon_id": _pick(row, "LogonID", "logon_id"),
        "scenario_name": _pick(row, "scenario_name", "scenario", "container.name"),
        "container_role": _pick(row, "container.role"),
        "catalog_metadata": context.metadata or None,
    }
    return merge_json_objects(metadata, empty_as_none=True)


def _resolve_netflow_labels(parser: BaseParser, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
    label_row = row
    if context.dataset_role == "TEST":
        label_row = {
            key: value
            for key, value in row.items()
            if key.lower() not in TEST_LABEL_FIELDS
        }
    return parser.label_resolver.resolve(label_row, context)  # type: ignore[attr-defined]


def _pick(row: dict[str, Any], *keys: str) -> Any:
    lowered = {key.lower(): value for key, value in row.items()}
    for key in keys:
        if key in row and row[key] not in ("", None):
            return row[key]
        value = lowered.get(key.lower())
        if value not in ("", None):
            return value
    return None


def _first_present_with_name(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[str | None, Any]:
    lowered = {key.lower(): (key, value) for key, value in row.items()}
    for field in fields:
        if field in row and row[field] not in ("", None):
            return field, row[field]
        resolved = lowered.get(field.lower())
        if resolved and resolved[1] not in ("", None):
            return str(resolved[0]), resolved[1]
    return None, None


def _sum_first_available(
    row: dict[str, Any],
    direct_fields: tuple[str, ...],
    paired_fields: tuple[tuple[str, str], ...],
) -> float | None:
    for fields in paired_fields:
        values = [_float_or_none(_pick(row, field)) for field in fields]
        present = [value for value in values if value is not None]
        if present:
            return float(sum(present))
    direct_values = [_float_or_none(_pick(row, field)) for field in direct_fields]
    present_direct = [value for value in direct_values if value is not None]
    if len(present_direct) > 1:
        return float(sum(present_direct))
    return present_direct[0] if present_direct else None


def _float_or_none(value: Any) -> float | None:
    if value in ("", None) or isinstance(value, bool):
        return None
    text = str(value).strip()
    if text.lower().startswith("port") and text[4:].isdigit():
        text = text[4:]
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    number = _float_or_none(value)
    if number is None:
        return None
    return int(number)


def _string_or_none(value: Any) -> str | None:
    return None if value in ("", None) else str(value)


def _looks_like_relative_number(value: Any) -> bool:
    return bool(NUMERIC_RE.match(str(value).strip())) if value not in ("", None) else False


def _float_or_text(value: Any) -> float | str | None:
    number = _float_or_none(value)
    if number is not None:
        return number
    return _string_or_none(value)


def _raw_preview(text: str) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= STAGE_TWO_MAX_RAW_PREVIEW_BYTES:
        return text
    return encoded[:STAGE_TWO_MAX_RAW_PREVIEW_BYTES].decode("utf-8", errors="replace")


def _line_preview_truncated(row: dict[str, Any]) -> bool | None:
    preview = row.get("_raw_line_preview")
    length = row.get("_raw_line_length")
    if preview is None or length is None:
        return None
    try:
        return int(length) > len(str(preview))
    except (TypeError, ValueError):
        return None


def _event_uid(context: ParserContext, index: int, entity_id: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{entity_id or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def _error_sample(row: dict[str, Any], exc: Exception) -> str:
    if row.get("_json_source_type"):
        compact = compact_json_row(row)
    else:
        compact = compact_row(row)
    return f"{type(exc).__name__}: {exc}; row={compact}"
