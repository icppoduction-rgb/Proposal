"""Markdown reports for Stage Three DNS feature extraction MVP."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.stage_three.extraction.base import FeatureExtractionResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK07_REPORT_FILENAME = "Task07-dns-feature-extractors-mvp.md"
PREVIOUS_REPORT_PATH = "Task06-feature-extraction-runtime-backend.md"


def save_dns_feature_extraction_reports(result: FeatureExtractionResult) -> FeatureExtractionResult:
    """Write RU and EN reports for DNS MVP feature extraction."""
    paths = build_stage_three_task_report_paths(TASK07_REPORT_FILENAME, create_dirs=True)
    enriched = replace(result, report_paths={"ru": str(paths.ru), "en": str(paths.en)})
    payload = enriched.to_dict()
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return enriched


def save_dns_feature_extraction_summary_reports(results: list[FeatureExtractionResult]) -> dict[str, str]:
    """Write one Task07 report that summarizes multiple DNS MVP feature groups."""
    if not results:
        raise ValueError("results must not be empty")
    paths = build_stage_three_task_report_paths(TASK07_REPORT_FILENAME, create_dirs=True)
    payload = _summary_payload(results, report_paths={"ru": str(paths.ru), "en": str(paths.en)})
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return payload["report_paths"]


def _summary_payload(results: list[FeatureExtractionResult], *, report_paths: dict[str, str]) -> dict[str, Any]:
    first = results[0]
    inputs_by_id: dict[int, dict[str, Any]] = {}
    outputs: list[dict[str, Any]] = []
    columns_created: list[str] = []
    missing_weighted: dict[str, float] = {}
    total_rows_written = 0
    peak_values: list[float] = []
    for result in results:
        for item in result.input_normalized_artifacts:
            inputs_by_id[item.artifact_id] = item.__dict__
        for output in result.output_feature_artifacts:
            outputs.append(output.__dict__)
            total_rows_written += output.rows_written
            if output.peak_rss_gb is not None:
                peak_values.append(output.peak_rss_gb)
        for column in result.columns_created:
            if column not in columns_created:
                columns_created.append(column)
            missing_weighted[column] = result.missing_ratios.get(column, 0.0)
    return {
        "status": "SUCCESS" if all(result.status == "SUCCESS" for result in results) else "PARTIAL_SUCCESS",
        "branch": first.branch,
        "role": first.role,
        "feature_group": ",".join(result.feature_group for result in results),
        "backend_used": first.backend_used,
        "input_normalized_artifacts": list(inputs_by_id.values()),
        "output_feature_artifacts": outputs,
        "rows_read": sum(result.rows_read for result in results),
        "rows_written": sum(result.rows_written for result in results),
        "columns_created": columns_created,
        "missing_ratios": missing_weighted,
        "runtime_seconds": sum(result.runtime_seconds for result in results),
        "peak_rss_gb": max(peak_values) if peak_values else None,
        "report_paths": report_paths,
    }


def _render_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 07 — dns-feature-extractors-mvp\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Feature group: `{payload['feature_group']}`\n"
        f"- Backend used: `{payload['backend_used']}`\n\n"
        "## Input normalized artifacts\n\n"
        f"{_items(_artifact_inputs(payload['input_normalized_artifacts']), empty='No input artifacts.')}\n\n"
        "## Output feature artifacts\n\n"
        f"{_items(_artifact_outputs(payload['output_feature_artifacts']), empty='No output artifacts.')}\n\n"
        "## Rows and columns\n\n"
        f"- Rows read: `{payload['rows_read']}`\n"
        f"- Rows written: `{payload['rows_written']}`\n"
        f"- Columns created: `{_json(payload['columns_created'])}`\n"
        f"- Missing ratios: `{_json(payload['missing_ratios'])}`\n\n"
        "## Runtime and memory metrics\n\n"
        f"- Runtime seconds: `{payload['runtime_seconds']}`\n"
        f"- Peak RSS GB: `{payload['peak_rss_gb']}`\n\n"
        "## Machine-readable details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 07 — dns-feature-extractors-mvp\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Feature group: `{payload['feature_group']}`\n"
        f"- Backend used: `{payload['backend_used']}`\n\n"
        "## Input Normalized Artifacts\n\n"
        f"{_items(_artifact_inputs(payload['input_normalized_artifacts']), empty='No input artifacts.')}\n\n"
        "## Output Feature Artifacts\n\n"
        f"{_items(_artifact_outputs(payload['output_feature_artifacts']), empty='No output artifacts.')}\n\n"
        "## Rows And Columns\n\n"
        f"- Rows read: `{payload['rows_read']}`\n"
        f"- Rows written: `{payload['rows_written']}`\n"
        f"- Columns created: `{_json(payload['columns_created'])}`\n"
        f"- Missing ratios: `{_json(payload['missing_ratios'])}`\n\n"
        "## Runtime And Memory Metrics\n\n"
        f"- Runtime seconds: `{payload['runtime_seconds']}`\n"
        f"- Peak RSS GB: `{payload['peak_rss_gb']}`\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _artifact_inputs(items: list[dict[str, Any]]) -> list[str]:
    return [
        f"artifact_id={item['artifact_id']}, dataset_id={item['dataset_id']}, path={item['normalized_path']}"
        for item in items
    ]


def _artifact_outputs(items: list[dict[str, Any]]) -> list[str]:
    return [
        f"normalized_artifact_id={item['normalized_artifact_id']}, rows={item['rows_written']}, path={item['feature_path']}"
        for item in items
    ]


def _items(items: list[str], *, empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- `{item}`" for item in items)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)
