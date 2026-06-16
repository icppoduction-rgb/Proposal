"""JSON helpers shared by Stage Two parser implementations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


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
