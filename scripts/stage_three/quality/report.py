"""Markdown reports for Stage Three quality checks."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.quality.runner import TASK18_PREVIOUS_REPORT_PATH, TASK18_REPORT_FILENAME, StageThreeQualityResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


def save_stage_three_quality_reports(result: StageThreeQualityResult) -> StageThreeQualityResult:
    """Write RU and EN Task18 quality reports."""
    paths = build_stage_three_task_report_paths(TASK18_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render(payload, title="Task 18 - stage-three-quality-checks"), encoding="utf-8")
    paths.en.write_text(_render(payload, title="Task 18 - stage-three-quality-checks"), encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _render(payload: dict[str, Any], *, title: str) -> str:
    return (
        f"# {title}\n\n"
        f"- Previous report path: `{TASK18_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Experiment ID: `{payload['experiment_id']}`\n"
        f"- Branch: `{payload.get('branch') or '*'}`\n"
        f"- Role: `{payload.get('role') or '*'}`\n"
        f"- Feature group: `{payload.get('feature_group') or '*'}`\n"
        f"- Feature artifacts checked: `{payload['feature_artifact_count']}`\n"
        f"- Model-ready artifacts checked: `{payload['model_ready_artifact_count']}`\n"
        f"- Preprocessing artifacts checked: `{payload['preprocessing_artifact_count']}`\n\n"
        "## Checks Executed\n\n"
        f"{_checks_executed(payload)}\n\n"
        "## PASS/WARN/FAIL Table\n\n"
        f"{_status_table(payload)}\n\n"
        "## Quality Report Catalog IDs\n\n"
        f"{_catalog_ids(payload)}\n\n"
        "## Blocking Issues\n\n"
        f"{_blocking_issues(payload)}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _checks_executed(payload: dict[str, Any]) -> str:
    names = sorted({f"{record['check_group']}.{record['check_name']}" for record in payload["checks"]})
    if not names:
        return "- `none`"
    return "\n".join(f"- `{name}`" for name in names)


def _status_table(payload: dict[str, Any]) -> str:
    rows = [
        "| check_group | check_name | artifact_type | artifact_id | status | severity | blocking | message |",
        "|---|---|---|---:|---|---|---:|---|",
    ]
    for record in payload["checks"]:
        rows.append(
            "| `{check_group}` | `{check_name}` | `{artifact_type}` | `{artifact_id}` | `{status}` | "
            "`{severity}` | `{blocking}` | {message} |".format(
                check_group=record["check_group"],
                check_name=record["check_name"],
                artifact_type=record["artifact_type"],
                artifact_id=record["artifact_id"] if record["artifact_id"] is not None else "",
                status=record["status"],
                severity=record["severity"],
                blocking=record["blocking"],
                message=str(record["message"]).replace("|", "\\|"),
            )
        )
    return "\n".join(rows)


def _catalog_ids(payload: dict[str, Any]) -> str:
    ids = [
        record["quality_report_id"]
        for record in payload["checks"]
        if record.get("quality_report_id") is not None
    ]
    if not ids:
        return "- `none`"
    return "\n".join(f"- `{value}`" for value in ids)


def _blocking_issues(payload: dict[str, Any]) -> str:
    issues = payload.get("blocking_issues", [])
    if not issues:
        return "- `none`"
    return "\n".join(f"- {issue}" for issue in issues)


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "experiment_id",
            "branch",
            "role",
            "feature_group",
            "feature_artifact_count",
            "model_ready_artifact_count",
            "preprocessing_artifact_count",
            "quality_report_ids",
            "blocking_issues",
            "checks",
            "report_paths",
        }
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
