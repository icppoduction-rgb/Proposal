"""Markdown reports for Stage Three feature catalog validation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.stage_three.feature_catalog.validator import FeatureCatalogValidationResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK05_REPORT_FILENAME = "Task05-feature-catalog-contract-validator.md"
PREVIOUS_REPORT_PATH = "Task04-stage-three-validate-inputs-readiness-gate.md"


def save_feature_catalog_reports(result: FeatureCatalogValidationResult) -> FeatureCatalogValidationResult:
    """Write RU and EN feature catalog validation reports."""
    paths = build_stage_three_task_report_paths(TASK05_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    enriched = replace(result, report_paths=report_paths)
    payload = enriched.to_dict()
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return enriched


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 05 — feature-catalog-contract-validator\n\n"
        f"- Предыдущий report: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Catalog version: `{payload['catalog_version']}`\n"
        f"- Validation result: `{payload['status']}`\n"
        f"- Normalized JSON snapshot: `{payload.get('normalized_snapshot_path') or ''}`\n\n"
        "## Feature groups\n\n"
        f"- Total: `{payload['feature_group_count']}`\n"
        f"- Features: `{payload['feature_count']}`\n"
        f"- Enabled: `{_json(payload['enabled_feature_groups'])}`\n"
        f"- Planned: `{_json(payload['planned_feature_groups'])}`\n\n"
        "## Forbidden X columns\n\n"
        f"{_items(payload['forbidden_X_columns'], empty='Forbidden X columns не заданы.')}\n\n"
        "## Validation issues\n\n"
        f"{_issues(payload['issues'])}\n\n"
        "## Machine-readable details\n\n"
        "```json\n"
        f"{_json(payload)}\n"
        "```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 05 — feature-catalog-contract-validator\n\n"
        f"- Previous report: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Catalog version: `{payload['catalog_version']}`\n"
        f"- Validation result: `{payload['status']}`\n"
        f"- Normalized JSON snapshot: `{payload.get('normalized_snapshot_path') or ''}`\n\n"
        "## Feature Groups\n\n"
        f"- Total: `{payload['feature_group_count']}`\n"
        f"- Features: `{payload['feature_count']}`\n"
        f"- Enabled: `{_json(payload['enabled_feature_groups'])}`\n"
        f"- Planned: `{_json(payload['planned_feature_groups'])}`\n\n"
        "## Forbidden X Columns\n\n"
        f"{_items(payload['forbidden_X_columns'], empty='No forbidden X columns configured.')}\n\n"
        "## Validation Issues\n\n"
        f"{_issues(payload['issues'])}\n\n"
        "## Machine-readable Details\n\n"
        "```json\n"
        f"{_json(payload)}\n"
        "```\n"
    )


def _items(items: list[str], *, empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- `{item}`" for item in items)


def _issues(issues: list[dict[str, str]]) -> str:
    if not issues:
        return "- No validation issues."
    return "\n".join(f"- `{issue['path']}`: {issue['message']}" for issue in issues)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)
