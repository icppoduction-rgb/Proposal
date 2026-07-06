"""Markdown reports for Stage Three model-ready tasks."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from scripts.stage_three.model_ready.separator import FeatureSeparationResult
from scripts.stage_three.model_ready.builder import (
    TASK17_PREVIOUS_REPORT_PATH,
    TASK17_REPORT_FILENAME,
    ModelReadyBuildResult,
    with_report_paths,
)
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


def save_model_ready_builder_reports(result: ModelReadyBuildResult) -> ModelReadyBuildResult:
    """Write RU and EN Task17 reports and return the result with report paths."""
    paths = build_stage_three_task_report_paths(TASK17_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    payload = {**result.to_dict(), "report_paths": report_paths}
    paths.ru.write_text(_render_model_ready_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_model_ready_en(payload), encoding="utf-8")
    return with_report_paths(result, report_paths)


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


def _render_model_ready_ru(payload: dict[str, Any]) -> str:
    return _render_model_ready(payload, title="Task 17 - model-ready-builder")


def _render_model_ready_en(payload: dict[str, Any]) -> str:
    return _render_model_ready(payload, title="Task 17 - model-ready-builder")


def _render_model_ready(payload: dict[str, Any], *, title: str) -> str:
    return (
        f"# {title}\n\n"
        f"- Previous report path: `{TASK17_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Experiment ID: `{payload['experiment_id']}`\n"
        f"- Branch: `{payload['branch']}`\n"
        f"- Preprocessing profile: `{payload['preprocessing_profile']}`\n"
        f"- Target: `{payload['target']}`\n"
        f"- Roles: `{', '.join(payload['roles'])}`\n"
        f"- Feature count: `{payload['feature_count']}`\n\n"
        "## Artifact Paths and Catalog IDs\n\n"
        f"{_model_ready_artifact_table(payload)}\n\n"
        "## X/y Row Counts\n\n"
        f"{_model_ready_row_counts(payload)}\n\n"
        "## Target Distribution\n\n"
        f"{_model_ready_target_distribution(payload)}\n\n"
        "## Split Index\n\n"
        f"```json\n{_json(payload.get('split_index_summary') or {})}\n```\n\n"
        "## X Schema\n\n"
        f"{_list_or_empty(payload['x_schema'])}\n\n"
        "## Warnings\n\n"
        f"{_list_or_empty(payload.get('warnings', []))}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(_compact_model_ready_payload(payload))}\n```\n"
    )


def _model_ready_artifact_table(payload: dict[str, Any]) -> str:
    rows = ["| role | data_type | catalog_id | path | resumed |", "|---|---:|---:|---|---:|"]
    for role_result in payload["role_results"]:
        for artifact in role_result["artifacts"]:
            rows.append(
                f"| `{role_result['role']}` | `{artifact['data_type']}` | "
                f"`{artifact['catalog_id']}` | `{artifact['artifact_path']}` | "
                f"`{artifact['resumed']}` |"
            )
        sequence_artifact = role_result.get("sequence_artifact")
        if sequence_artifact:
            rows.append(
                f"| `{role_result['role']}` | `{sequence_artifact['data_type']}` | "
                f"`{sequence_artifact['catalog_id']}` | `{sequence_artifact['artifact_path']}` | "
                f"`{sequence_artifact['resumed']}` |"
            )
    for key in ("split_index_artifact", "preprocessing_metadata_artifact"):
        artifact = payload.get(key)
        if artifact:
            rows.append(
                f"| `{artifact['role']}` | `{artifact['data_type']}` | "
                f"`{artifact['catalog_id']}` | `{artifact['artifact_path']}` | "
                f"`{artifact['resumed']}` |"
            )
    return "\n".join(rows)


def _model_ready_row_counts(payload: dict[str, Any]) -> str:
    rows = ["| role | X rows | y rows | feature_count |", "|---|---:|---:|---:|"]
    for role_result in payload["role_results"]:
        rows.append(
            f"| `{role_result['role']}` | `{role_result['x_row_count']}` | "
            f"`{role_result['y_row_count']}` | `{role_result['feature_count']}` |"
        )
    return "\n".join(rows)


def _model_ready_target_distribution(payload: dict[str, Any]) -> str:
    rows = ["| role | distribution |", "|---|---|"]
    for role_result in payload["role_results"]:
        rows.append(
            f"| `{role_result['role']}` | `{_json(role_result['target_distribution'])}` |"
        )
    return "\n".join(rows)


def _compact_model_ready_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key
        in {
            "status",
            "experiment_id",
            "branch",
            "preprocessing_profile",
            "target",
            "roles",
            "role_results",
            "split_index_artifact",
            "preprocessing_metadata_artifact",
            "split_index_summary",
            "feature_count",
            "x_schema",
            "warnings",
            "report_paths",
        }
    }
