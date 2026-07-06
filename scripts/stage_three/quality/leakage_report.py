"""Markdown reports for Stage Three leakage and traceability checks."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.quality.leakage import (
    TASK19_PREVIOUS_REPORT_PATH,
    TASK19_REPORT_FILENAME,
    StageThreeLeakageResult,
)
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


def save_stage_three_leakage_reports(result: StageThreeLeakageResult) -> StageThreeLeakageResult:
    """Write RU and EN Task19 leakage/traceability reports."""
    paths = build_stage_three_task_report_paths(TASK19_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    rendered = _render(payload)
    paths.ru.write_text(rendered, encoding="utf-8")
    paths.en.write_text(rendered, encoding="utf-8")
    return replace(result, report_paths=report_paths)


def _render(payload: dict[str, Any]) -> str:
    return (
        "# Task 19 - stage-three-leakage-and-traceability-checks\n\n"
        f"- Previous report path: `{TASK19_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Experiment ID: `{payload['experiment_id']}`\n"
        f"- Branch: `{payload.get('branch') or '*'}`\n"
        f"- Role: `{payload.get('role') or '*'}`\n"
        f"- Feature group: `{payload.get('feature_group') or '*'}`\n\n"
        "## Leakage Checks and Severity\n\n"
        f"{_checks_table(payload)}\n\n"
        "## Blocked Artifacts\n\n"
        f"{_blocked_artifacts(payload)}\n\n"
        "## Traceability Chain Examples\n\n"
        f"{_traceability_examples(payload)}\n\n"
        "## Missing Links\n\n"
        f"{_missing_links(payload)}\n\n"
        "## Quality Report Catalog IDs\n\n"
        f"{_quality_report_ids(payload)}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_payload(payload))}\n```\n"
    )


def _checks_table(payload: dict[str, Any]) -> str:
    rows = [
        "| check_group | check_name | artifact_id | status | severity | blocking | leakage_issue_count | message |",
        "|---|---|---:|---|---|---:|---:|---|",
    ]
    for record in payload["checks"]:
        rows.append(
            "| `{check_group}` | `{check_name}` | `{artifact_id}` | `{status}` | `{severity}` | "
            "`{blocking}` | `{leakage_issue_count}` | {message} |".format(
                check_group=record["check_group"],
                check_name=record["check_name"],
                artifact_id=record["artifact_id"] if record["artifact_id"] is not None else "",
                status=record["status"],
                severity=record["severity"],
                blocking=record["blocking"],
                leakage_issue_count=record["leakage_issue_count"] if record["leakage_issue_count"] is not None else "",
                message=str(record["message"]).replace("|", "\\|"),
            )
        )
    return "\n".join(rows)


def _blocked_artifacts(payload: dict[str, Any]) -> str:
    values = payload.get("blocked_artifact_ids", [])
    if not values:
        return "- `none`"
    return "\n".join(f"- `{artifact_id}`" for artifact_id in values)


def _traceability_examples(payload: dict[str, Any]) -> str:
    chains = payload.get("traceability_chains", [])[:5]
    if not chains:
        return "- `none`"
    rows = [
        "| model_ready | feature | normalized | parser_run | dataset_file | dataset | raw_source | status |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for chain in chains:
        rows.append(
            "| `{model}` | `{feature}` | `{normalized}` | `{parser}` | `{file}` | `{dataset}` | `{raw}` | `{status}` |".format(
                model=chain["model_ready_artifact_id"],
                feature=chain.get("feature_artifact_id") or "",
                normalized=chain.get("normalized_artifact_id") or "",
                parser=chain.get("parser_run_id") or "",
                file=chain.get("dataset_file_id") or "",
                dataset=chain.get("dataset_id") or "",
                raw=str(chain.get("raw_source_path") or "").replace("|", "\\|"),
                status=chain["status"],
            )
        )
    return "\n".join(rows)


def _missing_links(payload: dict[str, Any]) -> str:
    values = payload.get("missing_links", [])
    if not values:
        return "- `none`"
    return "\n".join(f"- `{value}`" for value in values)


def _quality_report_ids(payload: dict[str, Any]) -> str:
    values = payload.get("quality_report_ids", [])
    if not values:
        return "- `none`"
    return "\n".join(f"- `{value}`" for value in values)


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
            "checks",
            "traceability_chains",
            "blocked_artifact_ids",
            "missing_links",
            "quality_report_ids",
            "report_paths",
        }
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
