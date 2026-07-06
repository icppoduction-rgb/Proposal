"""Markdown reports for Stage Three label alignment policies."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.stage_three.labels.label_policy import LabelAlignmentOutput
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK10_REPORT_FILENAME = "Task10-label-alignment-policies.md"
PREVIOUS_REPORT_PATH = "Task09-feature-artifact-writer-and-catalog-registration.md"


def save_label_alignment_reports(result: LabelAlignmentOutput) -> LabelAlignmentOutput:
    """Write RU and EN Task10 reports for one label alignment result."""
    paths = build_stage_three_task_report_paths(TASK10_REPORT_FILENAME, create_dirs=True)
    payload = result.to_dict()
    payload["report_paths"] = {"ru": str(paths.ru), "en": str(paths.en)}
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return replace(result, summary={**result.summary, "report_paths": payload["report_paths"]})


def _render_ru(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return (
        "# Task 10 - label-alignment-policies\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `SUCCESS`\n"
        f"- Policy used: `{payload['policy']}`\n"
        f"- Sample level: `{payload['sample_level']}`\n\n"
        "## Label Coverage\n\n"
        f"- Samples: `{summary['sample_count']}`\n"
        f"- Labeled: `{summary['labeled_count']}`\n"
        f"- Coverage: `{summary['label_coverage']}`\n\n"
        "## Unlabeled/Conflicting Counts\n\n"
        f"- Unlabeled: `{summary['unlabeled_count']}`\n"
        f"- Conflicting: `{summary['conflicting_count']}`\n\n"
        "## Label Source/Status Distribution\n\n"
        f"- Source distribution: `{_json(summary['label_source_distribution'])}`\n"
        f"- Status distribution: `{_json(summary['label_status_distribution'])}`\n"
        f"- Binary distribution: `{_json(summary['label_binary_distribution'])}`\n\n"
        "## X/y/metadata Separation\n\n"
        f"- X rows: `{len(payload['x_rows'])}`\n"
        f"- y rows: `{len(payload['y_rows'])}`\n"
        f"- metadata rows: `{len(payload['metadata_rows'])}`\n"
        "- Label fields are kept out of X and preserved in y/metadata.\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return (
        "# Task 10 - label-alignment-policies\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `SUCCESS`\n"
        f"- Policy used: `{payload['policy']}`\n"
        f"- Sample level: `{payload['sample_level']}`\n\n"
        "## Label Coverage\n\n"
        f"- Samples: `{summary['sample_count']}`\n"
        f"- Labeled: `{summary['labeled_count']}`\n"
        f"- Coverage: `{summary['label_coverage']}`\n\n"
        "## Unlabeled/Conflicting Counts\n\n"
        f"- Unlabeled: `{summary['unlabeled_count']}`\n"
        f"- Conflicting: `{summary['conflicting_count']}`\n\n"
        "## Label Source/Status Distribution\n\n"
        f"- Source distribution: `{_json(summary['label_source_distribution'])}`\n"
        f"- Status distribution: `{_json(summary['label_status_distribution'])}`\n"
        f"- Binary distribution: `{_json(summary['label_binary_distribution'])}`\n\n"
        "## X/y/metadata Separation\n\n"
        f"- X rows: `{len(payload['x_rows'])}`\n"
        f"- y rows: `{len(payload['y_rows'])}`\n"
        f"- metadata rows: `{len(payload['metadata_rows'])}`\n"
        "- Label fields are kept out of X and preserved in y/metadata.\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)
