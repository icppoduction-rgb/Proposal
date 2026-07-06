"""Markdown reports for Task15 class balance and TRAIN-only balancing."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.preprocessing.class_balance import ClassBalanceReportResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK15_REPORT_FILENAME = "Task15-class-balance-report-and-train-only-balancing.md"
TASK15_PREVIOUS_REPORT_PATH = "Task14-scaling-profiles-and-preprocessing-artifacts.md"


def save_class_balance_reports(result: ClassBalanceReportResult) -> ClassBalanceReportResult:
    """Write RU and EN Task15 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK15_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 15 - class-balance-report-and-train-only-balancing\n\n"
        f"- Previous report path: `{TASK15_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Balancing method: `{payload['balancing_method']}`\n"
        f"- SMOTE enabled: `{payload['smote_enabled']}`\n"
        f"- VALIDATION/TEST not modified: `{payload['validation_test_not_modified']}`\n\n"
        "## Before/After Class Distribution\n\n"
        f"{_split_distributions(payload)}\n\n"
        "## Recommended Stage Four Class Metadata\n\n"
        f"{_class_weight_metadata(payload['class_weight_metadata'])}\n\n"
        "## VALIDATION/TEST Modification Guard\n\n"
        f"{_validation_test_guard(payload)}\n\n"
        "## Warnings\n\n"
        f"{_warnings(payload)}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 15 - class-balance-report-and-train-only-balancing\n\n"
        f"- Previous report path: `{TASK15_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Balancing method: `{payload['balancing_method']}`\n"
        f"- SMOTE enabled: `{payload['smote_enabled']}`\n"
        f"- VALIDATION/TEST not modified: `{payload['validation_test_not_modified']}`\n\n"
        "## Before/After Class Distribution\n\n"
        f"{_split_distributions(payload)}\n\n"
        "## Recommended Stage Four Class Metadata\n\n"
        f"{_class_weight_metadata(payload['class_weight_metadata'])}\n\n"
        "## VALIDATION/TEST Modification Guard\n\n"
        f"{_validation_test_guard(payload)}\n\n"
        "## Warnings\n\n"
        f"{_warnings(payload)}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _split_distributions(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    for role, result in payload["splits"].items():
        before = result["before_distribution"]
        after = result["after_distribution"]
        lines.append(
            "- `{role}`: rows `{rows_before}` -> `{rows_after}`, classes `{before_classes}` -> `{after_classes}`, "
            "missing labels `{missing_before}` -> `{missing_after}`".format(
                role=role,
                rows_before=result["rows_before"],
                rows_after=result["rows_after"],
                before_classes=_json(before["class_counts"]),
                after_classes=_json(after["class_counts"]),
                missing_before=before["missing_label_count"],
                missing_after=after["missing_label_count"],
            )
        )
    return "\n".join(lines)


def _class_weight_metadata(metadata: dict[str, Any]) -> str:
    return (
        f"- class_weight: `{_json(metadata['class_weight'])}`\n"
        f"- scale_pos_weight: `{metadata['scale_pos_weight']}`\n"
        f"- labeled_count: `{metadata['labeled_count']}`\n"
        f"- missing_label_count: `{metadata['missing_label_count']}`\n"
        f"- recommendation: `{metadata['recommendation']}`"
    )


def _validation_test_guard(payload: dict[str, Any]) -> str:
    validation = payload["splits"].get("VALIDATION", {})
    test = payload["splits"].get("TEST", {})
    return (
        f"- VALIDATION rows: `{validation.get('rows_before')}` -> `{validation.get('rows_after')}`; "
        f"modified=`{not validation.get('validation_test_not_modified', False)}`\n"
        f"- TEST rows: `{test.get('rows_before')}` -> `{test.get('rows_after')}`; "
        f"modified=`{not test.get('validation_test_not_modified', False)}`\n"
        "- No threshold tuning is performed by Task15."
    )


def _warnings(payload: dict[str, Any]) -> str:
    warnings = payload.get("warnings", [])
    if not warnings:
        return "- `none`"
    return "\n".join(f"- `{warning}`" for warning in warnings)


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "balancing_method",
            "splits",
            "class_weight_metadata",
            "validation_test_not_modified",
            "smote_enabled",
            "warnings",
            "report_paths",
        }
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
