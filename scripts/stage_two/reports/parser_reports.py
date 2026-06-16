"""Parser coverage and parser-run diagnostic report writers."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from config import (
    PATH_DATA_STORAGE,
    REPORTS_EN_STAGE_TWO,
    REPORTS_RU_STAGE_TWO,
    STAGE_TWO_MAX_ERROR_SAMPLES,
)
from scripts.db.models import DatasetFile, ParserRegistry, ParserRun
from scripts.stage_two.parsers.base import ParserResult


REPORT_FILE_BASENAME = "parser_coverage_matrix"
RUN_REPORT_WARNING_LIMIT = 50
RUN_REPORT_MESSAGE_CHAR_LIMIT = 1200
SAFE_PATH_SEGMENT_RE = re.compile(r"[^A-Za-z0-9_.=-]+")


def save_parser_coverage_reports(
    payload: dict[str, Any],
    *,
    storage_root: str | Path | None = None,
) -> dict[str, str]:
    """Write parser coverage JSON and Markdown reports under PATH_DATA_STORAGE."""
    root = _configured_storage_root(storage_root)
    paths = {
        "en_json": f"{REPORTS_EN_STAGE_TWO}/parser/{REPORT_FILE_BASENAME}.json",
        "ru_json": f"{REPORTS_RU_STAGE_TWO}/parser/{REPORT_FILE_BASENAME}.json",
        "en_md": f"{REPORTS_EN_STAGE_TWO}/parser/{REPORT_FILE_BASENAME}.md",
        "ru_md": f"{REPORTS_RU_STAGE_TWO}/parser/{REPORT_FILE_BASENAME}.md",
    }
    report_payload = {**payload, "report_paths": paths}
    for key in ("en_json", "ru_json"):
        path = root / paths[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    for language, key in (("en", "en_md"), ("ru", "ru_md")):
        path = root / paths[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render_markdown(language, report_payload), encoding="utf-8")
    return paths


def save_parser_run_reports(
    *,
    parser_run: ParserRun,
    dataset_file: DatasetFile,
    parser_result: ParserResult | None = None,
    parser_registry: ParserRegistry | None = None,
    output_artifact_path: str | None = None,
    error_message: str | None = None,
    storage_root: str | Path | None = None,
) -> dict[str, str]:
    """Write per-run parser and normalization diagnostic JSON reports."""
    root = _configured_storage_root(storage_root)
    paths = _parser_run_report_paths(parser_run, dataset_file)
    payload = _parser_run_report_payload(
        parser_run=parser_run,
        dataset_file=dataset_file,
        parser_result=parser_result,
        parser_registry=parser_registry,
        output_artifact_path=output_artifact_path,
        error_message=error_message,
        report_paths=paths,
    )
    for relative_path in paths.values():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=_json_default),
            encoding="utf-8",
        )
    return paths


def _configured_storage_root(storage_root: str | Path | None) -> Path:
    configured_value = storage_root if storage_root is not None else PATH_DATA_STORAGE
    if not str(configured_value).strip():
        raise ValueError("PATH_DATA_STORAGE must be configured for Stage Two reports.")
    return Path(configured_value).expanduser()


def _parser_run_report_paths(parser_run: ParserRun, dataset_file: DatasetFile) -> dict[str, str]:
    file_name = f"parser_run_{parser_run.id or 'pending'}.json"
    branch = _safe_path_segment(dataset_file.branch)
    role = _safe_path_segment(dataset_file.role)
    source_format = _safe_path_segment(dataset_file.source_format)
    tail = f"{branch}/{role}/{source_format}/{file_name}"
    return {
        "en_parser_json": f"{REPORTS_EN_STAGE_TWO}/parser/{tail}",
        "ru_parser_json": f"{REPORTS_RU_STAGE_TWO}/parser/{tail}",
        "en_normalization_json": f"{REPORTS_EN_STAGE_TWO}/normalization/{tail}",
        "ru_normalization_json": f"{REPORTS_RU_STAGE_TWO}/normalization/{tail}",
    }


def _parser_run_report_payload(
    *,
    parser_run: ParserRun,
    dataset_file: DatasetFile,
    parser_result: ParserResult | None,
    parser_registry: ParserRegistry | None,
    output_artifact_path: str | None,
    error_message: str | None,
    report_paths: dict[str, str],
) -> dict[str, Any]:
    warnings = _bounded_messages(
        parser_result.warnings if parser_result is not None else (),
        max_messages=RUN_REPORT_WARNING_LIMIT,
    )
    error_samples = _bounded_messages(
        parser_result.error_samples if parser_result is not None else (),
        max_messages=STAGE_TWO_MAX_ERROR_SAMPLES,
    )
    resolved_error_message = error_message or parser_run.error_message
    return {
        "report_type": "stage_two_parser_run_diagnostic",
        "parser_run_id": parser_run.id,
        "parser_registry_id": parser_run.parser_registry_id,
        "schema_version_id": parser_run.schema_version_id,
        "parser_name": parser_run.parser_name,
        "parser_version": parser_run.parser_version,
        "parser_module": getattr(parser_registry, "parser_module", None),
        "parser_class": getattr(parser_registry, "parser_class", None),
        "branch": dataset_file.branch,
        "role": dataset_file.role,
        "source_format": dataset_file.source_format,
        "dataset_id": dataset_file.dataset_id,
        "file_id": dataset_file.id,
        "source_file_path": dataset_file.file_path,
        "source_file_relative_path": dataset_file.relative_path,
        "source_file_hash": dataset_file.file_hash_sha256,
        "rows_read": _result_or_run_value(parser_result, parser_run, "rows_read"),
        "rows_parsed": _result_or_run_value(parser_result, parser_run, "rows_parsed"),
        "rows_failed": _result_or_run_value(parser_result, parser_run, "rows_failed"),
        "events_emitted": _events_emitted(parser_result, parser_run),
        "output_artifact_path": output_artifact_path or parser_run.output_parquet_path,
        "status": parser_run.status,
        "file_status": dataset_file.status,
        "warnings": warnings,
        "errors_sample": error_samples,
        "error_message": _truncate_message(resolved_error_message) if resolved_error_message else None,
        "read_hints": _read_hints(dataset_file, warnings),
        "schema_mismatch_counters": _schema_mismatch_counters(warnings, error_samples, resolved_error_message),
        "started_at": parser_run.started_at,
        "finished_at": parser_run.finished_at,
        "report_paths": report_paths,
    }


def _result_or_run_value(
    parser_result: ParserResult | None,
    parser_run: ParserRun,
    field_name: str,
) -> int | None:
    if parser_result is not None:
        return getattr(parser_result, field_name)
    return getattr(parser_run, field_name)


def _events_emitted(parser_result: ParserResult | None, parser_run: ParserRun) -> int | None:
    if parser_result is not None:
        return parser_result.events_emitted
    return parser_run.events_emitted


def _read_hints(dataset_file: DatasetFile, warnings: list[str]) -> dict[str, Any]:
    return {
        "encoding_hint": dataset_file.encoding_hint,
        "compression_hint": dataset_file.compression_hint or _warning_value(warnings, "compression_hint"),
        "base64_detected": any("base64_detected=True" in warning for warning in warnings),
        "decode_strategy": _decode_strategy_from_warnings(warnings),
    }


def _warning_value(warnings: list[str], key: str) -> str | None:
    prefix = f"{key}="
    for warning in warnings:
        if warning.startswith(prefix):
            return warning[len(prefix) :]
    return None


def _decode_strategy_from_warnings(warnings: list[str]) -> str | None:
    strategies: list[str] = []
    if any("base64_detected=True" in warning for warning in warnings):
        strategies.append("base64")
    compression = _warning_value(warnings, "compression_hint")
    if compression:
        strategies.append(f"compression:{compression}")
    return "|".join(strategies) if strategies else None


def _schema_mismatch_counters(
    warnings: list[str],
    error_samples: list[str],
    error_message: str | None,
) -> dict[str, int]:
    values = [*warnings, *error_samples]
    if error_message:
        values.append(error_message)
    normalized = [value.lower() for value in values]
    mismatch_markers = (
        "schema mismatch",
        "missing required",
        "missing fields",
        "required fields",
        "missing normalized",
    )
    return {
        "schema_mismatch": sum(
            1 for value in normalized if any(marker in value for marker in mismatch_markers)
        )
    }


def _bounded_messages(
    messages: list[str] | tuple[str, ...],
    *,
    max_messages: int,
) -> list[str]:
    return [_truncate_message(message) for message in messages[:max_messages]]


def _truncate_message(message: object) -> str:
    value = str(message)
    if len(value) <= RUN_REPORT_MESSAGE_CHAR_LIMIT:
        return value
    return f"{value[:RUN_REPORT_MESSAGE_CHAR_LIMIT]}...[truncated]"


def _safe_path_segment(value: object) -> str:
    segment = SAFE_PATH_SEGMENT_RE.sub("_", str(value).strip()).strip("._")
    return segment or "unknown"


def _json_default(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _render_markdown(language: str, payload: dict[str, Any]) -> str:
    title = (
        "Stage Two parser coverage matrix"
        if language == "en"
        else "Stage Two parser coverage matrix (ru)"
    )
    lines = [
        f"# {title}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Branch filter: `{payload.get('branch_filter') or 'all'}`",
        f"- Matrix rows: `{payload['summary']['matrix_rows']}`",
        f"- Catalog files: `{payload['summary']['catalog_files']}`",
        f"- Catalog gap rows: `{payload['summary']['catalog_gap_rows']}`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(payload["summary"], indent=2, sort_keys=True),
        "```",
        "",
        "## Matrix",
        "",
        "| branch | role | source_format | files_count | parser_active | parser_class | parser_name | action | diagnostics |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in payload["matrix"]:
        lines.append(
            "| {branch} | {role} | {source_format} | {files_count} | {parser_active} | "
            "{parser_class} | {parser_name} | {action} | {diagnostics} |".format(
                branch=_markdown_cell(row["branch"]),
                role=_markdown_cell(row["role"]),
                source_format=_markdown_cell(row["source_format"]),
                files_count=row["files_count"],
                parser_active="yes" if row["parser_active"] else "no",
                parser_class=_markdown_cell(row.get("parser_class") or ""),
                parser_name=_markdown_cell(row.get("parser_name") or ""),
                action=_markdown_cell(row["action"]),
                diagnostics=_markdown_cell("; ".join(row.get("diagnostics") or ())),
            )
        )
    lines.extend(
        [
            "",
            "## Stage One Diagnostics",
            "",
            "```json",
            json.dumps(payload["stage_one_diagnostics"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _markdown_cell(value: str) -> str:
    return str(value).replace("|", "\\|")
