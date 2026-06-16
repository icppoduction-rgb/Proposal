"""CSV helpers shared by Stage Two parser implementations."""

from __future__ import annotations

from itertools import zip_longest
from typing import Any, Iterable


EXTRA_COLUMNS_KEY = "_csv_extra_columns"


def clean_csv_key(key: Any) -> str:
    """Return a stable string key for CSV headers and generated field names."""
    return str(key or "").strip().lstrip("\ufeff")


def is_empty_csv_row(values: Iterable[Any]) -> bool:
    """Return True when a CSV row has no non-empty cell values."""
    return all(str(value or "").strip() == "" for value in values)


def compact_extra_columns(value: Any) -> list[Any]:
    """Normalize csv.DictReader extra columns into a compact list."""
    if isinstance(value, list):
        return [item for item in value if item not in ("", None)]
    return [] if value in ("", None) else [value]


def normalize_dict_row(row: dict[Any, Any]) -> dict[str, Any]:
    """Normalize DictReader rows and preserve unbound extra columns."""
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            extras = compact_extra_columns(value)
            if extras:
                normalized[EXTRA_COLUMNS_KEY] = extras
            continue
        normalized[clean_csv_key(key)] = value
    return normalized


def row_from_fieldnames(values: list[Any], fieldnames: tuple[str, ...] | list[str]) -> dict[str, Any]:
    """Build a row dictionary from positional CSV values."""
    row = {
        field_name: values[index] if index < len(values) else None
        for index, field_name in enumerate(fieldnames)
    }
    if len(values) > len(fieldnames):
        row[EXTRA_COLUMNS_KEY] = values[len(fieldnames) :]
    return normalize_dict_row(row)


def row_from_header(values: list[Any], header: tuple[str, ...] | list[str]) -> dict[str, Any]:
    """Build a row dictionary from a previously detected CSV header."""
    row: dict[Any, Any] = {}
    extras: list[Any] = []
    for key, value in zip_longest(header, values, fillvalue=None):
        if key is None:
            extras.append(value)
            continue
        row[key] = value
    if extras:
        row[None] = extras
    return normalize_dict_row(row)


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    """Drop empty values from a CSV row while preserving useful extras."""
    compact: dict[str, Any] = {}
    for key, value in row.items():
        if key == EXTRA_COLUMNS_KEY:
            extras = compact_extra_columns(value)
            if extras:
                compact[key] = extras
            continue
        if value in ("", None):
            continue
        if isinstance(value, list):
            extras = compact_extra_columns(value)
            if extras:
                compact[key] = extras
            continue
        compact[key] = value
    return compact


def looks_like_header(values: list[Any], known_fields: frozenset[str]) -> bool:
    """Return True when the first CSV row looks like a header row."""
    if not values or is_empty_csv_row(values):
        return False
    tokens = {clean_csv_key(value).lower() for value in values if clean_csv_key(value)}
    return bool(tokens.intersection(known_fields))


def first_present(row: dict[str, Any], fields: tuple[str, ...]) -> Any:
    """Return the first non-empty field, using case-insensitive fallback."""
    lowered = {key.lower(): value for key, value in row.items()}
    for field in fields:
        if field in row and row[field] not in ("", None):
            return row[field]
        value = lowered.get(field.lower())
        if value not in ("", None):
            return value
    return None


def first_present_with_name(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[str | None, Any]:
    """Return the source field name and value for the first non-empty field."""
    lowered = {key.lower(): (key, value) for key, value in row.items()}
    for field in fields:
        if field in row and row[field] not in ("", None):
            return field, row[field]
        resolved = lowered.get(field.lower())
        if resolved and resolved[1] not in ("", None):
            return str(resolved[0]), resolved[1]
    return None, None
