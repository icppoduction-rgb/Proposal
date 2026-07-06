"""Markdown reports for Task12 type casting and schema normalization."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.preprocessing.type_casting import TypeCastingResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK12_REPORT_FILENAME = "Task12-type-casting-and-schema-normalization.md"
PREVIOUS_REPORT_PATH = "Task11-xy-metadata-traceability-separation.md"


def save_type_casting_reports(result: TypeCastingResult) -> TypeCastingResult:
    """Write RU and EN Task12 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK12_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 12 - type-casting-and-schema-normalization\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Rows normalized: `{payload['row_count']}`\n"
        f"- Memory before: `{payload['memory_before_bytes']}` bytes\n"
        f"- Memory after: `{payload['memory_after_bytes']}` bytes\n\n"
        "## Dtype Conversions\n\n"
        f"{_conversions(payload)}\n\n"
        "## Rejected Columns\n\n"
        f"{_rejected(payload)}\n\n"
        "## Schema Warnings\n\n"
        f"{_warnings(payload)}\n\n"
        "## Schema Metadata\n\n"
        f"```json\n{_json(payload['schema_metadata'])}\n```\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 12 - type-casting-and-schema-normalization\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Rows normalized: `{payload['row_count']}`\n"
        f"- Memory before: `{payload['memory_before_bytes']}` bytes\n"
        f"- Memory after: `{payload['memory_after_bytes']}` bytes\n\n"
        "## Dtype Conversions\n\n"
        f"{_conversions(payload)}\n\n"
        "## Rejected Columns\n\n"
        f"{_rejected(payload)}\n\n"
        "## Schema Warnings\n\n"
        f"{_warnings(payload)}\n\n"
        "## Schema Metadata\n\n"
        f"```json\n{_json(payload['schema_metadata'])}\n```\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _conversions(payload: dict[str, Any]) -> str:
    conversions = payload.get("dtype_conversions", [])
    if not conversions:
        return "- `none`"
    return "\n".join(
        "- `{column}`: `{catalog_dtype}` -> `{output_dtype}`; action=`{action}`; memory `{before}` -> `{after}` bytes".format(
            column=item["column"],
            catalog_dtype=item["catalog_dtype"],
            output_dtype=item["output_dtype"],
            action=item["action"],
            before=item["memory_before_bytes"],
            after=item["memory_after_bytes"],
        )
        for item in conversions
    )


def _rejected(payload: dict[str, Any]) -> str:
    rejected = payload.get("rejected_columns", [])
    if not rejected:
        return "- `none`"
    return "\n".join(
        f"- `{item['column']}`: {item['reason']} (catalog_dtype=`{item.get('catalog_dtype')}`)"
        for item in rejected
    )


def _warnings(payload: dict[str, Any]) -> str:
    warnings = payload.get("schema_warnings", [])
    if not warnings:
        return "- `none`"
    return "\n".join(f"- `{item['column']}`: {item['message']}" for item in warnings)


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "row_count",
            "typed_columns",
            "dtype_conversions",
            "rejected_columns",
            "schema_warnings",
            "memory_before_bytes",
            "memory_after_bytes",
            "schema_metadata",
            "report_paths",
        }
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
