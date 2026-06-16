"""Safe Host XML parser for event-like XML sources."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import STAGE_TWO_MAX_RAW_PREVIEW_BYTES
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import merge_json_objects
from scripts.stage_two.parsers.input_reader import UniversalInputReader
from scripts.stage_two.parsers.json_utils import compact_json_row


UNSAFE_XML_DECLARATION_RE = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", flags=re.IGNORECASE)
EVENT_NODE_NAMES: frozenset[str] = frozenset(
    {
        "event",
        "record",
        "entry",
        "log",
        "item",
        "row",
        "alert",
    }
)
TIMESTAMP_FIELDS: tuple[str, ...] = (
    "@timestamp",
    "timestamp",
    "Timestamp",
    "System.TimeCreated.@SystemTime",
    "System.TimeCreated.SystemTime",
    "TimeCreated.@SystemTime",
    "TimeCreated.SystemTime",
    "event.timestamp",
    "EventTime",
    "Time",
    "Created",
    "DateTime",
)
HOST_FIELDS: tuple[str, ...] = (
    "host.name",
    "host",
    "Host",
    "hostname",
    "Computer",
    "System.Computer",
    "LogHost",
)
EVENT_ID_FIELDS: tuple[str, ...] = (
    "event_id",
    "event.code",
    "EventID",
    "EventId",
    "System.EventID",
    "System.EventId",
    "winlog.event_id",
)
USER_FIELDS: tuple[str, ...] = (
    "user.name",
    "user",
    "User",
    "username",
    "UserName",
    "SubjectUserName",
    "TargetUserName",
    "EventData.SubjectUserName",
    "EventData.TargetUserName",
)
PROCESS_NAME_FIELDS: tuple[str, ...] = (
    "process.name",
    "process",
    "Process",
    "ProcessName",
    "EventData.ProcessName",
    "Image",
)
PROCESS_ID_FIELDS: tuple[str, ...] = (
    "process.pid",
    "process_id",
    "ProcessID",
    "ProcessId",
    "System.Execution.@ProcessID",
    "System.Execution.ProcessID",
    "Execution.@ProcessID",
)
MESSAGE_FIELDS: tuple[str, ...] = (
    "message",
    "Message",
    "RenderingInfo.Message",
    "EventData.Message",
    "Description",
)
PROVIDER_FIELDS: tuple[str, ...] = (
    "Provider.@Name",
    "System.Provider.@Name",
    "Provider.Name",
    "System.Provider.Name",
    "Source",
)
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
    }
)


class HostXmlParser(BaseParser):
    """Parser for event-like Host XML without DTD/entity processing."""

    parser_name = "host_xml_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver(enable_filename_heuristics=False)

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse one XML file into normalized host events."""
        reader = UniversalInputReader(path)
        xml_parser = ET.XMLParser(target=ET.TreeBuilder())
        lines_seen = 0
        unsafe_error: str | None = None
        parse_error: str | None = None
        unsafe_probe_tail = ""

        with reader.iter_lines(keepends=True, skip_empty=False) as lines:
            for line_number, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                lines_seen += 1
                unsafe_probe = f"{unsafe_probe_tail}{line}"
                if UNSAFE_XML_DECLARATION_RE.search(unsafe_probe):
                    unsafe_error = f"line {line_number}: unsafe XML DTD/entity declaration rejected"
                    break
                unsafe_probe_tail = unsafe_probe[-128:]
                try:
                    xml_parser.feed(line)
                except ET.ParseError as exc:
                    parse_error = f"line {line_number}: XML parse error: {exc}"
                    break

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if reader_metadata.base64_detected:
            warnings.append("base64_detected=True")
        if reader_metadata.compression_hint:
            warnings.append(f"compression_hint={reader_metadata.compression_hint}")

        if unsafe_error is not None:
            warnings.append("unsafe_xml_rejected=True")
            return ParserResult(
                rows_read=1,
                rows_parsed=0,
                rows_failed=1,
                events=[],
                warnings=warnings,
                bytes_read=reader_metadata.bytes_read,
                error_samples=[unsafe_error],
            )
        if parse_error is not None:
            return ParserResult(
                rows_read=1,
                rows_parsed=0,
                rows_failed=1,
                events=[],
                warnings=warnings,
                bytes_read=reader_metadata.bytes_read,
                error_samples=[parse_error],
            )
        if lines_seen == 0:
            return ParserResult(
                rows_read=0,
                rows_parsed=0,
                rows_failed=0,
                events=[],
                warnings=warnings,
                bytes_read=reader_metadata.bytes_read,
            )

        try:
            root = xml_parser.close()
        except ET.ParseError as exc:
            return ParserResult(
                rows_read=1,
                rows_parsed=0,
                rows_failed=1,
                events=[],
                warnings=warnings,
                bytes_read=reader_metadata.bytes_read,
                error_samples=[f"XML parse error: {exc}"],
            )

        events: list[dict[str, Any]] = []
        rows_failed = 0
        error_samples: list[str] = []
        nodes = _event_nodes(root)
        for index, node in enumerate(nodes):
            row = _flatten_event_node(node)
            row["_xml_root_tag"] = _local_name(root.tag)
            row["_xml_event_tag"] = _local_name(node.tag)
            row["_xml_event_index"] = index
            try:
                events.append(_xml_row_to_event(self, row, index, context))
            except Exception as exc:
                rows_failed += 1
                error_samples.append(_error_sample(row, exc))

        result = ParserResult(
            rows_read=len(nodes),
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
        )
        self.validate_result(result)
        return result


def _xml_row_to_event(
    parser: BaseParser,
    row: dict[str, Any],
    index: int,
    context: ParserContext,
) -> dict[str, Any]:
    timestamp_source, timestamp = _timestamp_from_row(row)
    host_name = _string_or_none(_pick(row, *HOST_FIELDS))
    event_id = _string_or_none(_pick(row, *EVENT_ID_FIELDS))
    user_name = _string_or_none(_pick(row, *USER_FIELDS))
    process_name = _string_or_none(_pick(row, *PROCESS_NAME_FIELDS))
    process_id = _string_or_none(_pick(row, *PROCESS_ID_FIELDS))
    message = _string_or_none(_pick(row, *MESSAGE_FIELDS))
    provider = _string_or_none(_pick(row, *PROVIDER_FIELDS))
    event_type = _event_type(row, event_id=event_id)
    modality = "host_eventlog" if event_id or provider else "host_xml_event"
    entity_id = host_name or process_name or user_name or event_id or row.get("_xml_event_tag")
    label_fields = _resolve_xml_labels(parser, row, context)

    return parser.base_event(
        context,
        event_uid=_event_uid(context, index, entity_id or event_type),
        timestamp=timestamp,
        timestamp_source=timestamp_source if timestamp else None,
        timestamp_type="absolute" if timestamp else "event_order",
        event_index=index,
        entity_type="host",
        entity_id=entity_id,
        event_type=event_type,
        raw_event_name=provider or event_id or row.get("_xml_event_tag"),
        modality=modality,
        host_name=host_name,
        user_name=user_name,
        process_id=process_id,
        process_name=process_name,
        event_id=event_id,
        message=message,
        raw_fields_json=compact_json_row(row),
        metadata_json=_metadata(row, context, message=message, provider=provider),
        created_at=datetime.now(timezone.utc),
        **label_fields,
    )


def _event_nodes(root: ET.Element) -> list[ET.Element]:
    event_like = [node for node in root.iter() if _local_name(node.tag).lower() in EVENT_NODE_NAMES]
    if event_like:
        if event_like[0] is root:
            return event_like[1:] or [root]
        return event_like

    children = list(root)
    structured_children = [
        child
        for child in children
        if list(child) or child.attrib or _element_text(child) not in ("", None)
    ]
    if len(structured_children) > 1:
        return structured_children
    return [root]


def _flatten_event_node(node: ET.Element) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for attr_name, value in node.attrib.items():
        _store(row, f"@{_local_name(attr_name)}", value)
    text = _element_text(node)
    if text not in ("", None) and not list(node):
        _store(row, _local_name(node.tag), text)
    for child in node:
        _flatten_element(child, row, prefix="")
    return row


def _flatten_element(element: ET.Element, row: dict[str, Any], *, prefix: str) -> None:
    segment = _field_segment(element)
    path = f"{prefix}.{segment}" if prefix else segment
    for attr_name, value in element.attrib.items():
        attr_key = f"{path}.@{_local_name(attr_name)}"
        _store(row, attr_key, value)
    children = list(element)
    text = _element_text(element)
    if text not in ("", None):
        _store(row, path if not children else f"{path}._text", text)
    for child in children:
        _flatten_element(child, row, prefix=path)


def _field_segment(element: ET.Element) -> str:
    tag = _local_name(element.tag)
    name_attr = _attribute_value(element, "Name", "name")
    if tag.lower() == "data" and name_attr not in ("", None):
        return str(name_attr)
    return tag


def _attribute_value(element: ET.Element, *names: str) -> Any:
    lowered = {_local_name(key).lower(): value for key, value in element.attrib.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in ("", None):
            return value
    return None


def _store(row: dict[str, Any], key: str, value: Any) -> None:
    if value in ("", None):
        return
    if key not in row:
        row[key] = value
        return
    existing = row[key]
    if isinstance(existing, list):
        existing.append(value)
        return
    row[key] = [existing, value]


def _timestamp_from_row(row: dict[str, Any]) -> tuple[str | None, datetime | None]:
    for field in TIMESTAMP_FIELDS:
        source_name, value = _first_present_with_name(row, (field,))
        timestamp = _parse_timestamp(value)
        if timestamp is not None:
            return source_name, timestamp
    return None, None


def _parse_timestamp(value: Any) -> datetime | None:
    value = _first_scalar(value)
    if value in ("", None):
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is not None:
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        pass
    for format_string in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, format_string).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _event_type(row: dict[str, Any], *, event_id: str | None) -> str:
    explicit = _string_or_none(_pick(row, "event_type", "EventType", "event.action", "Task"))
    if explicit is not None:
        return explicit
    if event_id is not None:
        if _pick(row, "System.EventID", "System.Provider.@Name", "Provider.@Name") not in ("", None):
            return f"windows_event_{event_id}"
        return f"host_xml_event_{event_id}"
    tag = _string_or_none(row.get("_xml_event_tag"))
    return f"host_xml_{tag.lower()}" if tag else "host_xml_event"


def _metadata(
    row: dict[str, Any],
    context: ParserContext,
    *,
    message: str | None,
    provider: str | None,
) -> dict[str, Any] | None:
    metadata = {
        "source_format": context.source_format,
        "xml_root_tag": row.get("_xml_root_tag"),
        "xml_event_tag": row.get("_xml_event_tag"),
        "xml_event_index": row.get("_xml_event_index"),
        "provider": provider,
        "message_length": len(message) if message is not None else None,
        "catalog_metadata": context.metadata or None,
    }
    return merge_json_objects(metadata, empty_as_none=True)


def _resolve_xml_labels(parser: BaseParser, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
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
            return _first_scalar(row[key])
        value = lowered.get(key.lower())
        if value not in ("", None):
            return _first_scalar(value)
    return None


def _first_present_with_name(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[str | None, Any]:
    lowered = {key.lower(): (key, value) for key, value in row.items()}
    for field in fields:
        if field in row and row[field] not in ("", None):
            return field, _first_scalar(row[field])
        resolved = lowered.get(field.lower())
        if resolved and resolved[1] not in ("", None):
            return str(resolved[0]), _first_scalar(resolved[1])
    return None, None


def _first_scalar(value: Any) -> Any:
    if isinstance(value, list):
        for item in value:
            if item not in ("", None):
                return item
        return None
    return value


def _string_or_none(value: Any) -> str | None:
    value = _first_scalar(value)
    return None if value in ("", None) else str(value)


def _local_name(name: Any) -> str:
    text = str(name)
    if "}" in text:
        return text.rsplit("}", 1)[-1]
    return text


def _element_text(element: ET.Element) -> str | None:
    text = element.text.strip() if element.text else ""
    return text or None


def _event_uid(context: ParserContext, index: int, entity: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{entity or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def _raw_preview(value: str) -> str:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= STAGE_TWO_MAX_RAW_PREVIEW_BYTES:
        return value
    return encoded[:STAGE_TWO_MAX_RAW_PREVIEW_BYTES].decode("utf-8", errors="replace")


def _error_sample(row: dict[str, Any], exc: Exception) -> str:
    preview = _raw_preview(str(compact_json_row(row)))
    return f"{type(exc).__name__}: {exc}; row={preview}"
