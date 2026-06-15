"""Parser coverage report writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import PATH_DATA_STORAGE, REPORTS_EN_STAGE_TWO, REPORTS_RU_STAGE_TWO


REPORT_FILE_BASENAME = "parser_coverage_matrix"


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


def _configured_storage_root(storage_root: str | Path | None) -> Path:
    configured_value = storage_root if storage_root is not None else PATH_DATA_STORAGE
    if not str(configured_value).strip():
        raise ValueError("PATH_DATA_STORAGE must be configured for parser coverage reports.")
    return Path(configured_value).expanduser()


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
        "| branch | role | source_format | files_count | parser_active | parser_class | parser_name | action |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in payload["matrix"]:
        lines.append(
            "| {branch} | {role} | {source_format} | {files_count} | {parser_active} | "
            "{parser_class} | {parser_name} | {action} |".format(
                branch=_markdown_cell(row["branch"]),
                role=_markdown_cell(row["role"]),
                source_format=_markdown_cell(row["source_format"]),
                files_count=row["files_count"],
                parser_active="yes" if row["parser_active"] else "no",
                parser_class=_markdown_cell(row.get("parser_class") or ""),
                parser_name=_markdown_cell(row.get("parser_name") or ""),
                action=_markdown_cell(row["action"]),
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
