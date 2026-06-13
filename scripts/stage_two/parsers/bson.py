"""BSON sandbox telemetry parser for normalized host behaviour events."""

from __future__ import annotations

import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.dns import LabelResolverProtocol, UnlabeledResolver


EVENT_LIST_KEYS: tuple[str, ...] = ("calls", "events", "event_documents")
EVENT_NAME_KEYS: tuple[str, ...] = ("api", "call", "syscall", "syscall_name", "event", "operation", "category")


class HostBsonSandboxParser(BaseParser):
    """Parser for sandbox BSON process/API telemetry streams."""

    parser_name = "host_bson_sandbox_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse BSON documents into normalized sandbox behaviour events."""
        documents = list(_iter_bson_documents(Path(path).read_bytes()))
        events: list[dict[str, Any]] = []
        rows_failed = 0
        warnings: list[str] = []
        event_index = 0
        for document_index, document in enumerate(documents):
            try:
                for row in _iter_event_rows(document):
                    events.append(self._row_to_event(row, event_index, document_index, context))
                    event_index += 1
            except Exception as exc:
                rows_failed += 1
                warnings.append(f"document {document_index}: {exc}")
        result = ParserResult(
            rows_read=len(documents),
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
        )
        self.validate_result(result)
        return result

    def _row_to_event(
        self,
        row: dict[str, Any],
        event_index: int,
        document_index: int,
        context: ParserContext,
    ) -> dict[str, Any]:
        label_fields = self.label_resolver.resolve(row, context)
        event_name = _first_present(row, EVENT_NAME_KEYS) or "sandbox_event"
        absolute_timestamp = _parse_absolute_timestamp(_first_present(row, ("timestamp", "@timestamp", "datetime")))
        relative_time = _parse_float(_first_present(row, ("time", "relative_time", "relative_timestamp")))
        process_id = _string_or_none(_first_present(row, ("pid", "process_id", "process.pid")))
        process_name = _string_or_none(_first_present(row, ("process_name", "process.name", "process_path")))
        syscall_name = _string_or_none(_first_present(row, ("syscall", "syscall_name", "api")))
        return self.base_event(
            context,
            event_uid=_event_uid(context, event_index, event_name),
            timestamp=absolute_timestamp,
            timestamp_source="source_column" if absolute_timestamp else None,
            timestamp_type="absolute" if absolute_timestamp else ("relative" if relative_time is not None else "event_order"),
            event_index=event_index,
            entity_type="process" if process_id or process_name else "host",
            entity_id=process_id or process_name,
            event_type=str(event_name),
            raw_event_name=str(event_name),
            modality="sandbox",
            host_name=_string_or_none(_first_present(row, ("host", "host_name", "machine"))),
            process_id=process_id,
            process_name=process_name,
            parent_process_id=_string_or_none(_first_present(row, ("ppid", "parent_process_id"))),
            syscall_name=syscall_name,
            command_line=_string_or_none(_first_present(row, ("command_line", "cmdline"))),
            file_path=_string_or_none(_first_present(row, ("file_path", "path", "filepath"))),
            raw_fields_json=_compact_value(row),
            metadata_json={
                key: value
                for key, value in {
                    "document_index": document_index,
                    "relative_time": relative_time,
                    "thread_id": _first_present(row, ("tid", "thread_id")),
                    "category": _first_present(row, ("category",)),
                    "return_value": _first_present(row, ("return_value", "retval", "status")),
                }.items()
                if value not in ("", None)
            },
            created_at=datetime.now(timezone.utc),
            **label_fields,
        )


def _iter_bson_documents(data: bytes) -> Iterator[dict[str, Any]]:
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data):
            raise ValueError("truncated BSON document length")
        document, offset = _decode_document(data, offset)
        yield document


def _decode_document(data: bytes, offset: int) -> tuple[dict[str, Any], int]:
    if offset + 4 > len(data):
        raise ValueError("truncated BSON document")
    length = struct.unpack_from("<i", data, offset)[0]
    if length < 5 or offset + length > len(data):
        raise ValueError("invalid BSON document length")
    end = offset + length
    cursor = offset + 4
    document: dict[str, Any] = {}
    while cursor < end - 1:
        element_type = data[cursor]
        cursor += 1
        key, cursor = _read_cstring(data, cursor, end)
        value, cursor = _decode_value(element_type, data, cursor, end)
        document[key] = value
    if data[end - 1] != 0:
        raise ValueError("BSON document missing terminator")
    return document, end


def _decode_value(element_type: int, data: bytes, cursor: int, end: int) -> tuple[Any, int]:
    if element_type == 0x01:
        return struct.unpack_from("<d", data, cursor)[0], cursor + 8
    if element_type == 0x02:
        return _read_string(data, cursor, end)
    if element_type in (0x03, 0x04):
        value, next_cursor = _decode_document(data, cursor)
        if element_type == 0x04:
            return [value[key] for key in sorted(value, key=_array_sort_key)], next_cursor
        return value, next_cursor
    if element_type == 0x05:
        length = struct.unpack_from("<i", data, cursor)[0]
        subtype = data[cursor + 4]
        start = cursor + 5
        return {"bson_binary_subtype": subtype, "size": length}, start + length
    if element_type == 0x07:
        return data[cursor : cursor + 12].hex(), cursor + 12
    if element_type == 0x08:
        return data[cursor] == 1, cursor + 1
    if element_type == 0x09:
        milliseconds = struct.unpack_from("<q", data, cursor)[0]
        return datetime.fromtimestamp(milliseconds / 1000.0, tz=timezone.utc), cursor + 8
    if element_type == 0x0A:
        return None, cursor
    if element_type == 0x0B:
        pattern, cursor = _read_cstring(data, cursor, end)
        options, cursor = _read_cstring(data, cursor, end)
        return {"pattern": pattern, "options": options}, cursor
    if element_type == 0x10:
        return struct.unpack_from("<i", data, cursor)[0], cursor + 4
    if element_type == 0x11:
        return struct.unpack_from("<Q", data, cursor)[0], cursor + 8
    if element_type == 0x12:
        return struct.unpack_from("<q", data, cursor)[0], cursor + 8
    raise ValueError(f"unsupported BSON element type 0x{element_type:02x}")


def _read_cstring(data: bytes, cursor: int, end: int) -> tuple[str, int]:
    terminator = data.find(b"\x00", cursor, end)
    if terminator < 0:
        raise ValueError("unterminated BSON cstring")
    return data[cursor:terminator].decode("utf-8", errors="replace"), terminator + 1


def _read_string(data: bytes, cursor: int, end: int) -> tuple[str, int]:
    if cursor + 4 > end:
        raise ValueError("truncated BSON string length")
    length = struct.unpack_from("<i", data, cursor)[0]
    start = cursor + 4
    stop = start + length
    if length < 1 or stop > end:
        raise ValueError("invalid BSON string length")
    return data[start : stop - 1].decode("utf-8", errors="replace"), stop


def _array_sort_key(item: str) -> tuple[int, int | str]:
    if item.isdigit():
        return (0, int(item))
    return (1, item)


def _iter_event_rows(document: dict[str, Any]) -> Iterator[dict[str, Any]]:
    behaviour = _nested_get(document, "behavior.processes")
    if isinstance(behaviour, list):
        for process in behaviour:
            if not isinstance(process, dict):
                continue
            for call in _extract_nested_events(process):
                yield {**_process_context(process), **call}
        return
    yielded = False
    for row in _extract_nested_events(document):
        yielded = True
        yield row
    if not yielded:
        yield document


def _extract_nested_events(document: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for key in EVENT_LIST_KEYS:
        value = document.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return
    if any(key in document for key in EVENT_NAME_KEYS):
        yield document


def _process_context(process: dict[str, Any]) -> dict[str, Any]:
    keys = ("pid", "ppid", "process_id", "process_name", "process_path", "command_line")
    return {key: process[key] for key in keys if key in process}


def _nested_get(row: dict[str, Any], dotted_key: str) -> Any:
    current: Any = row
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = _nested_get(row, key) if "." in key else row.get(key)
        if value not in ("", None):
            return value
    return None


def _parse_absolute_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if value in ("", None):
        return None
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _parse_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return None if value in ("", None) else str(value)


def _compact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _compact_value(item) for key, item in value.items() if item not in ("", None)}
    if isinstance(value, list):
        return [_compact_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _event_uid(context: ParserContext, index: int, event_name: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{event_name or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()
