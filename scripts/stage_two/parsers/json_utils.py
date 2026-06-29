"""JSON helpers shared by Stage Two parser implementations."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any


MONGO_NUMBER_WRAPPER_RE = re.compile(
    r"\b(?P<name>NumberLong|NumberInt|NumberDouble)\(\s*(?P<value>\"[^\"\\]*(?:\\.[^\"\\]*)*\"|-?\d+(?:\.\d+)?)\s*\)"
)
MONGO_STRING_WRAPPER_RE = re.compile(
    r"\b(?P<name>ISODate|ObjectId)\(\s*(?P<value>\"[^\"\\]*(?:\\.[^\"\\]*)*\")\s*\)"
)


def loads_json_record(text: str) -> Any:
    """Load one JSON record, accepting common Mongo shell wrapper values.

    This helper keeps JSON parsing deterministic: it never evaluates code and
    only rewrites known scalar wrappers such as NumberLong("123") or
    ISODate("...") before retrying json.loads().
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        normalized = normalize_mongo_json_wrappers(text)
        if normalized == text:
            raise
        return json.loads(normalized)


def normalize_mongo_json_wrappers(text: str) -> str:
    """Return JSON text with safe Mongo shell scalar wrappers converted."""

    def replace_number(match: re.Match[str]) -> str:
        raw_value = match.group("value")
        if raw_value.startswith('"'):
            try:
                decoded = json.loads(raw_value)
            except json.JSONDecodeError:
                return raw_value
            if re.fullmatch(r"-?\d+(?:\.\d+)?", str(decoded)):
                return str(decoded)
            return json.dumps(decoded, ensure_ascii=False)
        return raw_value

    def replace_string(match: re.Match[str]) -> str:
        return match.group("value")

    normalized = MONGO_NUMBER_WRAPPER_RE.sub(replace_number, text)
    normalized = MONGO_STRING_WRAPPER_RE.sub(replace_string, normalized)
    return normalized


def flatten_json_object(value: Any, *, separator: str = ".") -> dict[str, Any]:
    """Flatten a JSON object into dotted keys suitable for raw_fields_json."""
    if isinstance(value, Mapping):
        flattened: dict[str, Any] = {}
        _flatten_mapping(value, flattened, prefix="", separator=separator)
        return flattened
    return {
        "_json_scalar_type": type(value).__name__,
        "_json_scalar_value": _json_safe_value(value),
        "message": json.dumps(value, ensure_ascii=False),
    }


def compact_json_row(row: dict[str, Any]) -> dict[str, Any]:
    """Drop empty JSON values while keeping JSON-safe nested structures."""
    compact: dict[str, Any] = {}
    for key, value in row.items():
        if value in ("", None):
            continue
        if isinstance(value, Mapping):
            nested = compact_json_row({str(item_key): item_value for item_key, item_value in value.items()})
            if nested:
                compact[str(key)] = nested
            continue
        if isinstance(value, list):
            items = [_json_safe_value(item) for item in value if item not in ("", None)]
            if items:
                compact[str(key)] = items
            continue
        compact[str(key)] = _json_safe_value(value)
    return compact


def _flatten_mapping(
    value: Mapping[Any, Any],
    output: dict[str, Any],
    *,
    prefix: str,
    separator: str,
) -> None:
    for raw_key, item in value.items():
        key = str(raw_key)
        dotted_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(item, Mapping):
            _flatten_mapping(item, output, prefix=dotted_key, separator=separator)
            continue
        output[dotted_key] = _json_safe_value(item)


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    return value
