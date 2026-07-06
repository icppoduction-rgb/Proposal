"""Markdown reports for Task11 X/y/metadata/traceability separation."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.model_ready.separator import FeatureSeparationResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK11_REPORT_FILENAME = "Task11-xy-metadata-traceability-separation.md"
PREVIOUS_REPORT_PATH = "Task10-label-alignment-policies.md"


def save_xy_separation_reports(result: FeatureSeparationResult) -> FeatureSeparationResult:
    """Write RU and EN Task11 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK11_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 11 - xy-metadata-traceability-separation\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Rows separated: `{payload['row_count']}`\n"
        f"- Forbidden X columns check: `PASSED`\n\n"
        "## X Columns Kept\n\n"
        f"{_list_or_empty(payload['x_columns'])}\n\n"
        "## y Columns\n\n"
        f"{_list_or_empty(payload['y_columns'])}\n\n"
        "## Metadata Columns\n\n"
        f"{_list_or_empty(payload['metadata_columns'])}\n\n"
        "## Traceability Columns\n\n"
        f"{_list_or_empty(payload['traceability_columns'])}\n\n"
        "## Dropped/Forbidden Columns\n\n"
        f"{_dropped_columns(payload)}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 11 - xy-metadata-traceability-separation\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Rows separated: `{payload['row_count']}`\n"
        f"- Forbidden X columns check: `PASSED`\n\n"
        "## X Columns Kept\n\n"
        f"{_list_or_empty(payload['x_columns'])}\n\n"
        "## y Columns\n\n"
        f"{_list_or_empty(payload['y_columns'])}\n\n"
        "## Metadata Columns\n\n"
        f"{_list_or_empty(payload['metadata_columns'])}\n\n"
        "## Traceability Columns\n\n"
        f"{_list_or_empty(payload['traceability_columns'])}\n\n"
        "## Dropped/Forbidden Columns\n\n"
        f"{_dropped_columns(payload)}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _list_or_empty(values: list[str]) -> str:
    if not values:
        return "- `none`"
    return "\n".join(f"- `{value}`" for value in values)


def _dropped_columns(payload: dict[str, Any]) -> str:
    dropped = payload.get("dropped_columns", [])
    if not dropped:
        return "- `none`"
    return "\n".join(f"- `{item['name']}`: {item['reason']}" for item in dropped)


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "row_count",
            "source_columns",
            "x_columns",
            "y_columns",
            "metadata_columns",
            "traceability_columns",
            "dropped_columns",
            "forbidden_x_columns",
            "report_paths",
        }
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
