"""BSON sandbox telemetry parser for normalized host behaviour events."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from config import STAGE_TWO_MAX_RAW_PREVIEW_BYTES
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import merge_json_objects
from scripts.stage_two.parsers.input_reader import InputReaderError, UniversalInputReader


EVENT_LIST_KEYS: tuple[str, ...] = ("calls", "events", "event_documents", "apicalls")
EVENT_NAME_KEYS: tuple[str, ...] = (
    "api",
    "call",
    "syscall",
    "syscall_name",
    "event",
    "operation",
    "name",
)
DESCRIPTOR_ID_KEYS: tuple[str, ...] = (
    "descriptor_id",
    "event_descriptor_id",
    "api_id",
    "apiid",
    "call_id",
    "callid",
    "I",
    "id",
)
EVENT_ID_KEYS: tuple[str, ...] = ("event_id", "event.id", "h", "H", "id")
PROCESS_ID_KEYS: tuple[str, ...] = ("pid", "process_id", "process.pid", "P", "ProcessId")
THREAD_ID_KEYS: tuple[str, ...] = ("tid", "thread_id", "thread.id", "T", "ThreadId")
PARENT_PROCESS_ID_KEYS: tuple[str, ...] = ("ppid", "parent_process_id", "parent.pid", "ParentProcessId")
PROCESS_NAME_KEYS: tuple[str, ...] = (
    "process_name",
    "process.name",
    "process_path",
    "process.path",
    "image",
    "Image",
)
COMMAND_LINE_KEYS: tuple[str, ...] = ("command_line", "cmdline", "cmd", "CommandLine")
MODULE_PATH_KEYS: tuple[str, ...] = ("module_path", "module.path", "module", "dll_path", "ImageLoaded")
FILE_PATH_KEYS: tuple[str, ...] = (
    "file_path",
    "filepath",
    "path",
    "pathname",
    "file.name",
    "FileName",
    "TargetFilename",
)
TIMESTAMP_KEYS: tuple[str, ...] = ("timestamp", "@timestamp", "datetime", "event.timestamp")
RELATIVE_TIME_KEYS: tuple[str, ...] = ("t", "time", "relative_time", "relative_timestamp", "elapsed")
ARGUMENT_KEYS: tuple[str, ...] = ("arguments", "args", "params", "A")
BSON_TEST_LABEL_FIELDS: frozenset[str] = frozenset(
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
        "exploit",
    }
)


class BsonDecodeError(ValueError):
    """Raised when one BSON document cannot be safely decoded."""


@dataclass(frozen=True)
class Descriptor:
    """Sandbox event descriptor mapped by descriptor/event id."""

    descriptor_id: str
    name: str | None
    category: str | None
    descriptor_type: str | None
    argument_names: tuple[str, ...]
    raw: dict[str, Any]


class HostBsonSandboxParser(BaseParser):
    """Parser for sandbox BSON process/API telemetry streams."""

    parser_name = "host_bson_sandbox_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse BSON documents into normalized sandbox behaviour events."""
        reader = UniversalInputReader(path)
        events: list[dict[str, Any]] = []
        warnings: list[str] = []
        error_samples: list[str] = []
        rows_read = 0
        rows_failed = 0
        event_index = 0
        descriptors: dict[str, Descriptor] = {}
        descriptor_documents = 0

        try:
            binary_type = reader.detect_binary_type()
            if binary_type != "bson_stream":
                message = f"unsupported BSON binary type: {binary_type}"
                reader_metadata = reader.metadata_snapshot()
                result = ParserResult(
                    rows_read=0,
                    rows_parsed=0,
                    rows_failed=1,
                    events=[],
                    warnings=[*reader_metadata.warnings, message],
                    bytes_read=reader_metadata.bytes_read,
                    error_samples=[message],
                )
                self.validate_result(result)
                return result

            with reader.open("bson_stream") as bson_documents:
                for document_index, document_bytes in enumerate(bson_documents):
                    rows_read += 1
                    try:
                        document, _offset = _decode_document(document_bytes, 0)
                    except Exception as exc:
                        rows_failed += 1
                        message = f"document {document_index}: {exc}"
                        warnings.append(message)
                        error_samples.append(message)
                        continue

                    descriptor = _descriptor_from_document(document)
                    if descriptor is not None:
                        descriptors[descriptor.descriptor_id] = descriptor
                        descriptor_documents += 1
                        continue
                    descriptor_collection = _descriptor_collection(document)
                    if descriptor_collection:
                        descriptors.update(descriptor_collection)
                        descriptor_documents += len(descriptor_collection)
                        continue

                    try:
                        emitted = False
                        for row_index, row in enumerate(_iter_event_rows(document)):
                            descriptor = descriptors.get(_descriptor_id(row) or "")
                            events.append(
                                self._row_to_event(
                                    row,
                                    event_index=event_index,
                                    document_index=document_index,
                                    row_index=row_index,
                                    descriptor=descriptor,
                                    context=context,
                                )
                            )
                            event_index += 1
                            emitted = True
                        if not emitted:
                            warnings.append(f"document {document_index}: no event rows emitted")
                    except Exception as exc:
                        rows_failed += 1
                        message = f"document {document_index}: {exc}"
                        warnings.append(message)
                        error_samples.append(message)
        except InputReaderError as exc:
            rows_failed += 1
            message = f"failed to read BSON stream: {exc}"
            warnings.append(message)
            error_samples.append(message)

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
            *warnings,
        ]
        if reader_metadata.base64_detected:
            warnings.append("base64_detected=True")
        if descriptor_documents:
            warnings.append(f"descriptor_documents={descriptor_documents}")
        if descriptors:
            warnings.append(f"descriptors_mapped={len(descriptors)}")

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

    def _row_to_event(
        self,
        row: dict[str, Any],
        *,
        event_index: int,
        document_index: int,
        row_index: int,
        descriptor: Descriptor | None,
        context: ParserContext,
    ) -> dict[str, Any]:
        label_fields = self.label_resolver.resolve(_label_safe_row(row, context), context)
        descriptor_id = _descriptor_id(row)
        event_id = _event_id(row, descriptor_id=descriptor_id)
        event_name = _event_name(row, descriptor) or "sandbox_event"
        category = _string_or_none(_first_present(row, ("category", "event.category"))) or (
            descriptor.category if descriptor is not None else None
        )
        absolute_timestamp = _parse_absolute_timestamp(_first_present(row, TIMESTAMP_KEYS))
        relative_time = _parse_float(_first_present(row, RELATIVE_TIME_KEYS))
        mapped_arguments = _mapped_arguments(_first_present(row, ARGUMENT_KEYS), descriptor)
        process_id = _string_or_none(_first_present(row, PROCESS_ID_KEYS))
        process_name = _string_or_none(_first_present(row, PROCESS_NAME_KEYS)) or _string_from_args(
            mapped_arguments,
            ("process_name", "process", "image", "Image"),
        )
        file_path = _string_or_none(_first_present(row, FILE_PATH_KEYS)) or _path_from_args(mapped_arguments)
        command_line = _string_or_none(_first_present(row, COMMAND_LINE_KEYS)) or _string_from_args(
            mapped_arguments,
            ("command_line", "cmdline", "cmd", "CommandLine"),
        )
        module_path = _string_or_none(_first_present(row, MODULE_PATH_KEYS)) or _string_from_args(
            mapped_arguments,
            ("module_path", "module", "dll_path", "ImageLoaded"),
        )
        return self.base_event(
            context,
            event_uid=_event_uid(context, event_index, descriptor_id or event_name),
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
            parent_process_id=_string_or_none(_first_present(row, PARENT_PROCESS_ID_KEYS)),
            syscall_name=_string_or_none(_first_present(row, ("syscall", "syscall_name", "api"))) or str(event_name),
            event_id=event_id,
            command_line=command_line,
            file_path=file_path or module_path,
            raw_fields_json=_event_raw_fields(row, descriptor=descriptor, mapped_arguments=mapped_arguments),
            metadata_json=_event_metadata(
                row,
                descriptor=descriptor,
                descriptor_id=descriptor_id,
                event_id=event_id,
                category=category,
                document_index=document_index,
                row_index=row_index,
                relative_time=relative_time,
                module_path=module_path,
                mapped_arguments=mapped_arguments,
            ),
            created_at=datetime.now(timezone.utc),
            **label_fields,
        )


def _decode_document(data: bytes, offset: int) -> tuple[dict[str, Any], int]:
    if offset + 4 > len(data):
        raise BsonDecodeError("truncated BSON document")
    length = struct.unpack_from("<i", data, offset)[0]
    if length < 5 or offset + length > len(data):
        raise BsonDecodeError(f"invalid BSON document length {length}")
    end = offset + length
    cursor = offset + 4
    document: dict[str, Any] = {}
    while cursor < end - 1:
        element_type = data[cursor]
        cursor += 1
        key, cursor = _read_cstring(data, cursor, end)
        value, cursor = _decode_value(element_type, data, cursor, end, field_name=key)
        document[key] = value
    if data[end - 1] != 0:
        raise BsonDecodeError("BSON document missing terminator")
    return document, end


def _decode_value(
    element_type: int,
    data: bytes,
    cursor: int,
    end: int,
    *,
    field_name: str,
) -> tuple[Any, int]:
    if element_type == 0x01:
        _require_available(data, cursor, 8, end, field_name)
        return struct.unpack_from("<d", data, cursor)[0], cursor + 8
    if element_type in (0x02, 0x0D, 0x0E):
        return _read_string(data, cursor, end)
    if element_type in (0x03, 0x04):
        value, next_cursor = _decode_document(data, cursor)
        if element_type == 0x04:
            return [value[key] for key in sorted(value, key=_array_sort_key)], next_cursor
        return value, next_cursor
    if element_type == 0x05:
        _require_available(data, cursor, 5, end, field_name)
        length = struct.unpack_from("<i", data, cursor)[0]
        subtype = data[cursor + 4]
        start = cursor + 5
        if length < 0 or start + length > end:
            raise BsonDecodeError(f"invalid BSON binary length for field {field_name}: {length}")
        return {"bson_binary_subtype": subtype, "size": length}, start + length
    if element_type in (0x06, 0x0A, 0xFF, 0x7F):
        return None, cursor
    if element_type == 0x07:
        _require_available(data, cursor, 12, end, field_name)
        return data[cursor : cursor + 12].hex(), cursor + 12
    if element_type == 0x08:
        _require_available(data, cursor, 1, end, field_name)
        return data[cursor] == 1, cursor + 1
    if element_type == 0x09:
        _require_available(data, cursor, 8, end, field_name)
        milliseconds = struct.unpack_from("<q", data, cursor)[0]
        return datetime.fromtimestamp(milliseconds / 1000.0, tz=timezone.utc), cursor + 8
    if element_type == 0x0B:
        pattern, cursor = _read_cstring(data, cursor, end)
        options, cursor = _read_cstring(data, cursor, end)
        return {"pattern": pattern, "options": options}, cursor
    if element_type == 0x0C:
        namespace, cursor = _read_string(data, cursor, end)
        _require_available(data, cursor, 12, end, field_name)
        return {"namespace": namespace, "object_id": data[cursor : cursor + 12].hex()}, cursor + 12
    if element_type == 0x0F:
        _require_available(data, cursor, 4, end, field_name)
        scoped_length = struct.unpack_from("<i", data, cursor)[0]
        if scoped_length < 14 or cursor + scoped_length > end:
            raise BsonDecodeError(f"invalid javascript scope length for field {field_name}: {scoped_length}")
        return {"javascript_scope_bytes": scoped_length}, cursor + scoped_length
    if element_type == 0x10:
        _require_available(data, cursor, 4, end, field_name)
        return struct.unpack_from("<i", data, cursor)[0], cursor + 4
    if element_type == 0x11:
        _require_available(data, cursor, 8, end, field_name)
        increment, timestamp = struct.unpack_from("<II", data, cursor)
        return {"increment": increment, "timestamp": timestamp}, cursor + 8
    if element_type == 0x12:
        _require_available(data, cursor, 8, end, field_name)
        return struct.unpack_from("<q", data, cursor)[0], cursor + 8
    if element_type == 0x13:
        _require_available(data, cursor, 16, end, field_name)
        return {"decimal128": data[cursor : cursor + 16].hex()}, cursor + 16
    raise BsonDecodeError(f"unsupported BSON element type 0x{element_type:02x} for field {field_name}")


def _require_available(data: bytes, cursor: int, size: int, end: int, field_name: str) -> None:
    if cursor + size > min(len(data), end):
        raise BsonDecodeError(f"truncated BSON value for field {field_name}")


def _read_cstring(data: bytes, cursor: int, end: int) -> tuple[str, int]:
    terminator = data.find(b"\x00", cursor, end)
    if terminator < 0:
        raise BsonDecodeError("unterminated BSON cstring")
    return data[cursor:terminator].decode("utf-8", errors="replace"), terminator + 1


def _read_string(data: bytes, cursor: int, end: int) -> tuple[str, int]:
    _require_available(data, cursor, 4, end, "string")
    length = struct.unpack_from("<i", data, cursor)[0]
    start = cursor + 4
    stop = start + length
    if length < 1 or stop > end:
        raise BsonDecodeError(f"invalid BSON string length {length}")
    return data[start : stop - 1].decode("utf-8", errors="replace"), stop


def _array_sort_key(item: str) -> tuple[int, int | str]:
    if item.isdigit():
        return (0, int(item))
    return (1, item)


def _descriptor_from_document(document: dict[str, Any]) -> Descriptor | None:
    nested = document.get("descriptor")
    if isinstance(nested, dict):
        return _descriptor_from_document(nested)
    descriptors = _descriptor_collection(document)
    if descriptors:
        return None
    descriptor_id = _descriptor_id(document)
    if descriptor_id is None:
        return None
    name = _string_or_none(_first_present(document, ("name", "api", "call", "event", "operation")))
    category = _string_or_none(_first_present(document, ("category", "event.category")))
    descriptor_type = _string_or_none(_first_present(document, ("type", "descriptor_type")))
    if name is None or not any(key in document for key in ("args", "arguments", "category", "type", "flags_value", "flags_bitmask")):
        return None
    return Descriptor(
        descriptor_id=descriptor_id,
        name=name,
        category=category,
        descriptor_type=descriptor_type,
        argument_names=_argument_names(_first_present(document, ARGUMENT_KEYS)),
        raw=_compact_value(document),
    )


def _descriptor_collection(document: dict[str, Any]) -> dict[str, Descriptor]:
    collections = (
        document.get("descriptors"),
        document.get("api_descriptors"),
        document.get("syscall_descriptors"),
        document.get("event_descriptors"),
    )
    descriptors: dict[str, Descriptor] = {}
    for collection in collections:
        if isinstance(collection, dict):
            for key, value in collection.items():
                payload = value if isinstance(value, dict) else {"I": key, "name": value}
                payload = {**payload, "I": payload.get("I", key)}
                descriptor = _descriptor_from_document(payload)
                if descriptor is not None:
                    descriptors[descriptor.descriptor_id] = descriptor
        if isinstance(collection, list):
            for item in collection:
                if isinstance(item, dict):
                    descriptor = _descriptor_from_document(item)
                    if descriptor is not None:
                        descriptors[descriptor.descriptor_id] = descriptor
    return descriptors


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
    if not yielded and _looks_like_event_document(document):
        yield document


def _extract_nested_events(document: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for key in EVENT_LIST_KEYS:
        value = document.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return
    if _looks_like_event_document(document):
        yield document


def _looks_like_event_document(document: dict[str, Any]) -> bool:
    if document.get("_descriptor_only"):
        return False
    if _descriptor_from_document(document) is not None:
        return False
    return any(key in document for key in (*EVENT_NAME_KEYS, "I", "event_id", "args", "arguments"))


def _process_context(process: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "pid",
        "ppid",
        "process_id",
        "process_name",
        "process_path",
        "command_line",
        "cmdline",
        "host",
        "host_name",
    )
    return {key: process[key] for key in keys if key in process}


def _descriptor_id(row: dict[str, Any]) -> str | None:
    return _string_or_none(_first_present(row, DESCRIPTOR_ID_KEYS))


def _event_id(row: dict[str, Any], *, descriptor_id: str | None) -> str | None:
    value = _first_present(row, EVENT_ID_KEYS)
    if value in ("", None):
        return descriptor_id
    return _string_or_none(value)


def _event_name(row: dict[str, Any], descriptor: Descriptor | None) -> str | None:
    explicit = _string_or_none(_first_present(row, EVENT_NAME_KEYS))
    if explicit is not None:
        return explicit
    return descriptor.name if descriptor is not None else None


def _mapped_arguments(value: Any, descriptor: Descriptor | None) -> dict[str, Any] | None:
    if value in ("", None):
        return None
    if isinstance(value, dict):
        return _compact_value(value)
    if isinstance(value, list):
        names = descriptor.argument_names if descriptor is not None else ()
        mapped: dict[str, Any] = {}
        for index, item in enumerate(value):
            name = names[index] if index < len(names) and names[index] else f"arg_{index}"
            mapped[name] = _compact_value(item)
        return mapped
    return {"arg_0": _compact_value(value)}


def _argument_names(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    names: list[str] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            name = _string_or_none(_first_present(item, ("name", "arg_name", "field", "key")))
        else:
            name = _string_or_none(item)
        names.append(name or f"arg_{index}")
    return tuple(names)


def _event_raw_fields(
    row: dict[str, Any],
    *,
    descriptor: Descriptor | None,
    mapped_arguments: dict[str, Any] | None,
) -> dict[str, Any]:
    descriptor_fields = {
        "descriptor_name": descriptor.name if descriptor is not None else None,
        "descriptor_category": descriptor.category if descriptor is not None else None,
        "descriptor_type": descriptor.descriptor_type if descriptor is not None else None,
    }
    return merge_json_objects(
        _compact_value(row),
        descriptor_fields,
        {"mapped_arguments": mapped_arguments},
        empty_as_none=False,
    ) or {}


def _event_metadata(
    row: dict[str, Any],
    *,
    descriptor: Descriptor | None,
    descriptor_id: str | None,
    event_id: str | None,
    category: str | None,
    document_index: int,
    row_index: int,
    relative_time: float | None,
    module_path: str | None,
    mapped_arguments: dict[str, Any] | None,
) -> dict[str, Any] | None:
    metadata = {
        "document_index": document_index,
        "document_row_index": row_index,
        "descriptor_id": descriptor_id,
        "event_id": event_id,
        "descriptor_type": descriptor.descriptor_type if descriptor is not None else None,
        "category": category,
        "relative_time": relative_time,
        "thread_id": _first_present(row, THREAD_ID_KEYS),
        "counter": _first_present(row, ("h", "counter", "event_counter")),
        "return_value": _first_present(row, ("return_value", "retval", "status")),
        "module_path": module_path,
        "arguments_count": len(mapped_arguments) if mapped_arguments is not None else None,
    }
    return merge_json_objects(metadata, empty_as_none=True)


def _label_safe_row(row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
    if context.dataset_role != "TEST":
        return row
    return {
        key: value
        for key, value in row.items()
        if key.lower() not in BSON_TEST_LABEL_FIELDS
    }


def _path_from_args(arguments: dict[str, Any] | None) -> str | None:
    if not arguments:
        return None
    return _string_from_args(
        arguments,
        (
            "path",
            "file_path",
            "filepath",
            "pathname",
            "module_path",
            "image",
            "Image",
            "FileName",
            "TargetFilename",
        ),
    )


def _string_from_args(arguments: dict[str, Any] | None, keys: tuple[str, ...]) -> str | None:
    if not arguments:
        return None
    lowered = {key.lower(): value for key, value in arguments.items()}
    for key in keys:
        value = arguments.get(key, lowered.get(key.lower()))
        if value not in ("", None) and not isinstance(value, (dict, list)):
            return str(value)
    return None


def _nested_get(row: dict[str, Any], dotted_key: str) -> Any:
    current: Any = row
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    lowered = {key.lower(): (key, value) for key, value in row.items()}
    for key in keys:
        value = _nested_get(row, key) if "." in key else row.get(key)
        if value not in ("", None):
            return value
        resolved = lowered.get(key.lower())
        if resolved and resolved[1] not in ("", None):
            return resolved[1]
    return None


def _parse_absolute_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if value in ("", None):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
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
        return {
            str(key): _compact_value(item)
            for key, item in value.items()
            if item not in ("", None) and not str(key).startswith("_descriptor_only")
        }
    if isinstance(value, list):
        return [_compact_value(item) for item in value if item not in ("", None)]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        encoded = value.encode("utf-8", errors="replace")
        if len(encoded) > STAGE_TWO_MAX_RAW_PREVIEW_BYTES:
            return {
                "preview": encoded[:STAGE_TWO_MAX_RAW_PREVIEW_BYTES].decode("utf-8", errors="replace"),
                "length": len(value),
                "truncated": True,
            }
    return value


def _event_uid(context: ParserContext, index: int, event_name: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{event_name or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()
