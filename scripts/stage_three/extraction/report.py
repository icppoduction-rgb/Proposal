"""Markdown reports for Stage Three DNS feature extraction MVP."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.stage_three.extraction.base import FeatureExtractionResult
from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths


TASK07_REPORT_FILENAME = "Task07-dns-feature-extractors-mvp.md"
TASK08_REPORT_FILENAME = "Task08-host-network-feature-extractors-core.md"
TASK09_REPORT_FILENAME = "Task09-feature-artifact-writer-and-catalog-registration.md"
PREVIOUS_REPORT_PATH = "Task06-feature-extraction-runtime-backend.md"
TASK08_PREVIOUS_REPORT_PATH = "Task07-dns-feature-extractors-mvp.md"
TASK09_PREVIOUS_REPORT_PATH = "Task08-host-network-feature-extractors-core.md"
TASK08_SUPPORTED_FEATURE_GROUPS = (
    "host_syscall",
    "host_process",
    "host_auth",
    "host_file_access",
    "host_metrics",
    "host_logs",
    "network_flow",
    "network_ports",
    "network_protocol",
    "network_direction",
    "network_timing",
)


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


def save_host_network_feature_extraction_reports(result: FeatureExtractionResult) -> FeatureExtractionResult:
    """Write RU and EN reports for Task08 Host/Network core feature extraction."""
    paths = build_stage_three_task_report_paths(TASK08_REPORT_FILENAME, create_dirs=True)
    enriched = replace(result, report_paths={"ru": str(paths.ru), "en": str(paths.en)})
    payload = enriched.to_dict()
    paths.ru.write_text(_render_task08_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_task08_en(payload), encoding="utf-8")
    return enriched


def save_host_network_feature_extraction_summary_reports(results: list[FeatureExtractionResult]) -> dict[str, str]:
    """Write one Task08 report summarizing multiple Host/Network feature groups."""
    if not results:
        raise ValueError("results must not be empty")
    paths = build_stage_three_task_report_paths(TASK08_REPORT_FILENAME, create_dirs=True)
    payload = _summary_payload(results, report_paths={"ru": str(paths.ru), "en": str(paths.en)})
    paths.ru.write_text(_render_task08_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_task08_en(payload), encoding="utf-8")
    return payload["report_paths"]


def save_feature_artifact_registration_reports(result: FeatureExtractionResult) -> FeatureExtractionResult:
    """Write RU and EN reports for Task09 feature artifact registration."""
    paths = build_stage_three_task_report_paths(TASK09_REPORT_FILENAME, create_dirs=True)
    enriched = replace(result, report_paths={"ru": str(paths.ru), "en": str(paths.en)})
    payload = enriched.to_dict()
    paths.ru.write_text(_render_task09_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_task09_en(payload), encoding="utf-8")
    return enriched


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
        "warnings": _unique([warning for result in results for warning in result.warnings]),
        "runtime_stats": {
            "artifact_count": len(outputs),
            "batch_count": sum(
                int(output.get("runtime_stats", {}).get("batch_count", 0))
                for output in outputs
            ),
        },
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


def _render_task08_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 08 - host-network-feature-extractors-core\n\n"
        f"- Previous report path: `{TASK08_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Feature group: `{payload['feature_group']}`\n"
        f"- Backend used: `{payload['backend_used']}`\n\n"
        "## Поддерживаемые Feature Groups\n\n"
        f"{_items(list(TASK08_SUPPORTED_FEATURE_GROUPS), empty='No supported groups.')}\n\n"
        "## Входные Normalized Artifacts\n\n"
        f"{_items(_artifact_inputs(payload['input_normalized_artifacts']), empty='No input artifacts.')}\n\n"
        "## Выходные Feature Artifacts\n\n"
        f"{_items(_artifact_outputs(payload['output_feature_artifacts']), empty='No output artifacts.')}\n\n"
        "## Unsupported/Partial Fields\n\n"
        f"{_items(payload.get('warnings', []), empty='No unsupported source fields were observed.')}\n\n"
        "## Строки и Колонки\n\n"
        f"- Rows read: `{payload['rows_read']}`\n"
        f"- Rows written: `{payload['rows_written']}`\n"
        f"- Columns created: `{_json(payload['columns_created'])}`\n"
        f"- Missing ratios: `{_json(payload['missing_ratios'])}`\n\n"
        "## Runtime и Memory Metrics\n\n"
        f"- Runtime seconds: `{payload['runtime_seconds']}`\n"
        f"- Peak RSS GB: `{payload['peak_rss_gb']}`\n"
        f"- Runtime stats: `{_json(payload.get('runtime_stats', {}))}`\n\n"
        "## Quality Warnings\n\n"
        f"{_items(payload.get('warnings', []), empty='No quality warnings.')}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _render_task08_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 08 - host-network-feature-extractors-core\n\n"
        f"- Previous report path: `{TASK08_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Feature group: `{payload['feature_group']}`\n"
        f"- Backend used: `{payload['backend_used']}`\n\n"
        "## Supported Feature Groups\n\n"
        f"{_items(list(TASK08_SUPPORTED_FEATURE_GROUPS), empty='No supported groups.')}\n\n"
        "## Input Normalized Artifacts\n\n"
        f"{_items(_artifact_inputs(payload['input_normalized_artifacts']), empty='No input artifacts.')}\n\n"
        "## Output Feature Artifacts\n\n"
        f"{_items(_artifact_outputs(payload['output_feature_artifacts']), empty='No output artifacts.')}\n\n"
        "## Unsupported/Partial Fields\n\n"
        f"{_items(payload.get('warnings', []), empty='No unsupported source fields were observed.')}\n\n"
        "## Rows And Columns\n\n"
        f"- Rows read: `{payload['rows_read']}`\n"
        f"- Rows written: `{payload['rows_written']}`\n"
        f"- Columns created: `{_json(payload['columns_created'])}`\n"
        f"- Missing ratios: `{_json(payload['missing_ratios'])}`\n\n"
        "## Runtime And Memory Metrics\n\n"
        f"- Runtime seconds: `{payload['runtime_seconds']}`\n"
        f"- Peak RSS GB: `{payload['peak_rss_gb']}`\n"
        f"- Runtime stats: `{_json(payload.get('runtime_stats', {}))}`\n\n"
        "## Quality Warnings\n\n"
        f"{_items(payload.get('warnings', []), empty='No quality warnings.')}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _render_task09_ru(payload: dict[str, Any]) -> str:
    return (
        "# Task 09 - feature-artifact-writer-and-catalog-registration\n\n"
        f"- Previous report path: `{TASK09_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Feature group: `{payload['feature_group']}`\n\n"
        "## Written Artifact Paths\n\n"
        f"{_items(_task09_artifact_paths(payload['output_feature_artifacts']), empty='No artifacts were written in this run.')}\n\n"
        "## Catalog IDs\n\n"
        f"{_items([str(item) for item in payload.get('registered_catalog_ids', [])], empty='No catalog rows were registered in this run.')}\n\n"
        "## Row/Column Counts\n\n"
        f"{_items(_task09_counts(payload['output_feature_artifacts']), empty='No row/column counts available.')}\n\n"
        "## Traceability\n\n"
        f"{_items(_task09_traceability(payload['output_feature_artifacts']), empty='No traceability rows were registered.')}\n\n"
        "## Resume Behavior\n\n"
        f"- Resume skipped count: `{payload.get('resume_skipped_count', 0)}`\n"
        f"{_items(_task09_skipped(payload.get('skipped_feature_artifacts', [])), empty='No artifacts were skipped by resume.')}\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _render_task09_en(payload: dict[str, Any]) -> str:
    return (
        "# Task 09 - feature-artifact-writer-and-catalog-registration\n\n"
        f"- Previous report path: `{TASK09_PREVIOUS_REPORT_PATH}`\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch/role: `{payload['branch']}/{payload['role']}`\n"
        f"- Feature group: `{payload['feature_group']}`\n\n"
        "## Written Artifact Paths\n\n"
        f"{_items(_task09_artifact_paths(payload['output_feature_artifacts']), empty='No artifacts were written in this run.')}\n\n"
        "## Catalog IDs\n\n"
        f"{_items([str(item) for item in payload.get('registered_catalog_ids', [])], empty='No catalog rows were registered in this run.')}\n\n"
        "## Row/Column Counts\n\n"
        f"{_items(_task09_counts(payload['output_feature_artifacts']), empty='No row/column counts available.')}\n\n"
        "## Traceability\n\n"
        f"{_items(_task09_traceability(payload['output_feature_artifacts']), empty='No traceability rows were registered.')}\n\n"
        "## Resume Behavior\n\n"
        f"- Resume skipped count: `{payload.get('resume_skipped_count', 0)}`\n"
        f"{_items(_task09_skipped(payload.get('skipped_feature_artifacts', [])), empty='No artifacts were skipped by resume.')}\n\n"
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


def _task09_artifact_paths(items: list[dict[str, Any]]) -> list[str]:
    outputs: list[str] = []
    for item in items:
        parts = item.get("parts") or []
        if parts:
            outputs.extend(str(part) for part in parts)
        else:
            outputs.append(str(item.get("feature_path", "")))
    return outputs


def _task09_counts(items: list[dict[str, Any]]) -> list[str]:
    return [
        "catalog_id={catalog_id}, normalized_artifact_id={normalized_id}, rows={rows}, columns={columns}".format(
            catalog_id=item.get("catalog_artifact_id"),
            normalized_id=item.get("normalized_artifact_id"),
            rows=item.get("rows_written"),
            columns=item.get("column_count") or len(item.get("columns_created") or []),
        )
        for item in items
    ]


def _task09_traceability(items: list[dict[str, Any]]) -> list[str]:
    return [
        "catalog_id={catalog_id} -> normalized_artifact_ids={source_ids}".format(
            catalog_id=item.get("catalog_artifact_id"),
            source_ids=_json(item.get("source_artifact_ids") or [item.get("normalized_artifact_id")]),
        )
        for item in items
    ]


def _task09_skipped(items: list[dict[str, Any]]) -> list[str]:
    return [
        "catalog_id={catalog_id}, normalized_artifact_id={normalized_id}, reason={reason}".format(
            catalog_id=item.get("catalog_artifact_id"),
            normalized_id=item.get("normalized_artifact_id"),
            reason=item.get("reason"),
        )
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


def _unique(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values
