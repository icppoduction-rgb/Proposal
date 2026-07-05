"""Markdown reports for Stage Three validate-inputs readiness gate."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.stage_three.readiness.validator import StageThreeReadinessResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK04_REPORT_FILENAME = "Task04-stage-three-validate-inputs-readiness-gate.md"
PREVIOUS_REPORT_PATH = "Task03-stage-three-cli-skeleton.md"


def save_validate_inputs_reports(
    result: StageThreeReadinessResult,
    *,
    filename: str = TASK04_REPORT_FILENAME,
) -> StageThreeReadinessResult:
    """Write RU and EN readiness reports and return result with paths attached."""
    paths = build_stage_three_task_report_paths(filename, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    enriched = replace(result, report_paths=report_paths)
    payload = enriched.to_dict()
    paths.ru.write_text(_render_markdown("ru", payload), encoding="utf-8")
    paths.en.write_text(_render_markdown("en", payload), encoding="utf-8")
    return enriched


def _render_markdown(language: str, payload: dict[str, Any]) -> str:
    if language == "ru":
        return _render_ru(payload)
    return _render_en(payload)


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 04 — Stage Three validate-inputs readiness gate\n\n"
        f"- Предыдущий report: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Итоговый статус: `{payload['status']}`\n"
        f"- Проверенные branch/role: `{_json(payload['checked_branches_roles'])}`\n"
        f"- Количество normalized artifacts: `{payload['normalized_artifact_count']}`\n\n"
        "## Сводка по каталогам\n\n"
        f"- normalized_artifacts by status: `{_json(payload['normalized_artifacts_by_status'])}`\n"
        f"- parser_runs by status: `{_json(payload['parser_runs_by_status'])}`\n"
        f"- dataset_files by status: `{_json(payload['dataset_files_by_status'])}`\n\n"
        "## PASS/WARN/FAIL проверки\n\n"
        f"{_checks_table(payload['checks'])}\n\n"
        "## Blocking issues\n\n"
        f"{_items(payload['blocking_issues'], empty='Blocking issues не найдены.')}\n\n"
        "## Next actions\n\n"
        f"{_items(payload['next_actions'], empty='Дополнительные действия не требуются.')}\n\n"
        "## Machine-readable details\n\n"
        "```json\n"
        f"{_json(payload)}\n"
        "```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 04 — Stage Three validate-inputs readiness gate\n\n"
        f"- Previous report: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Final status: `{payload['status']}`\n"
        f"- Checked branch/role: `{_json(payload['checked_branches_roles'])}`\n"
        f"- Normalized artifact count: `{payload['normalized_artifact_count']}`\n\n"
        "## Catalog Summary\n\n"
        f"- normalized_artifacts by status: `{_json(payload['normalized_artifacts_by_status'])}`\n"
        f"- parser_runs by status: `{_json(payload['parser_runs_by_status'])}`\n"
        f"- dataset_files by status: `{_json(payload['dataset_files_by_status'])}`\n\n"
        "## PASS/WARN/FAIL Checks\n\n"
        f"{_checks_table(payload['checks'])}\n\n"
        "## Blocking Issues\n\n"
        f"{_items(payload['blocking_issues'], empty='No blocking issues found.')}\n\n"
        "## Next Actions\n\n"
        f"{_items(payload['next_actions'], empty='No further action required.')}\n\n"
        "## Machine-readable Details\n\n"
        "```json\n"
        f"{_json(payload)}\n"
        "```\n"
    )


def _checks_table(checks: list[dict[str, Any]]) -> str:
    lines = ["| Check | Status | Blocking | Message |", "| --- | --- | --- | --- |"]
    for check in checks:
        lines.append(
            "| "
            f"{check['name']} | "
            f"{check['status']} | "
            f"{'yes' if check['blocking'] else 'no'} | "
            f"{_escape_table(str(check['message']))} |"
        )
    return "\n".join(lines)


def _items(items: list[str], *, empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")
