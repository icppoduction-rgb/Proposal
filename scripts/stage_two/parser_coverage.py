"""Parser coverage diagnostics for Stage Two catalog files."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import SORT_PATH_DNS_FILE, SORT_PATH_HOST_FILE
from scripts.db import session_scope
from scripts.db.models import DatasetFile, ParserRegistry
from scripts.db.models.constants import BRANCH_VALUES, ROLE_VALUES
from scripts.stage_two.parser_registry import ParserResolver, validate_parser_registry_row
from scripts.stage_two.reports.parser_reports import save_parser_coverage_reports


CoverageKey = tuple[str, str, str]


@dataclass(frozen=True)
class ParserCoverageRow:
    """One branch/role/source_format coverage row."""

    branch: str
    role: str
    source_format: str
    files_count: int
    parser_active: bool
    parser_class: str | None
    parser_name: str | None
    parser_version: str | None
    registry_is_active: bool | None
    supported_role: str | None
    action: str
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParserCoverageResult:
    """Serializable parser coverage matrix result."""

    status: str
    branch_filter: str | None
    summary: dict[str, Any]
    matrix: tuple[ParserCoverageRow, ...]
    stage_one_diagnostics: dict[str, Any]
    report_paths: dict[str, str]


class ParserCoverageService:
    """Build parser coverage matrix from catalog counts and parser registry."""

    def __init__(self, session: Session) -> None:
        """Initialize service with an externally managed session."""
        self.session = session
        self.resolver = ParserResolver(session)

    def build(self, *, branch: str | None = None) -> ParserCoverageResult:
        """Build coverage matrix without writing reports."""
        _validate_branch_filter(branch)
        catalog_counts = self._catalog_file_counts(branch=branch)
        registry_rows = self._registry_rows(branch=branch)
        matrix_keys = self._matrix_keys(catalog_counts, registry_rows)
        rows = tuple(
            self._coverage_row(
                key,
                files_count=catalog_counts.get(key, 0),
                registry_rows=registry_rows,
            )
            for key in sorted(matrix_keys, key=_coverage_key_sort)
        )
        summary = _coverage_summary(rows, registry_rows)
        return ParserCoverageResult(
            status="SUCCESS"
            if summary["catalog_gap_rows"] == 0 and summary["missing_parser_rows"] == 0
            else "FAILED",
            branch_filter=branch,
            summary=summary,
            matrix=rows,
            stage_one_diagnostics=load_stage_one_diagnostics(branch=branch),
            report_paths={},
        )

    def _catalog_file_counts(self, *, branch: str | None) -> dict[CoverageKey, int]:
        statement = (
            select(
                DatasetFile.branch,
                DatasetFile.role,
                DatasetFile.source_format,
                func.count().label("files_count"),
            )
            .group_by(DatasetFile.branch, DatasetFile.role, DatasetFile.source_format)
            .order_by(DatasetFile.branch, DatasetFile.role, DatasetFile.source_format)
        )
        if branch is not None:
            statement = statement.where(DatasetFile.branch == branch)
        rows = self.session.execute(statement).all()
        return {
            (row.branch, row.role, row.source_format): int(row.files_count)
            for row in rows
        }

    def _registry_rows(self, *, branch: str | None) -> tuple[ParserRegistry, ...]:
        statement = select(ParserRegistry).order_by(
            ParserRegistry.branch.asc(),
            ParserRegistry.source_format.asc(),
            ParserRegistry.supported_role.asc().nullsfirst(),
            ParserRegistry.priority.asc(),
            ParserRegistry.id.asc(),
        )
        if branch is not None:
            statement = statement.where(ParserRegistry.branch == branch)
        return tuple(self.session.execute(statement).scalars().all())

    def _matrix_keys(
        self,
        catalog_counts: dict[CoverageKey, int],
        registry_rows: tuple[ParserRegistry, ...],
    ) -> set[CoverageKey]:
        keys = set(catalog_counts)
        for registry_row in registry_rows:
            for role in _roles_for_registry_row(registry_row):
                keys.add((registry_row.branch, role, registry_row.source_format))
        return keys

    def _coverage_row(
        self,
        key: CoverageKey,
        *,
        files_count: int,
        registry_rows: tuple[ParserRegistry, ...],
    ) -> ParserCoverageRow:
        branch, role, source_format = key
        resolution = self.resolver.resolve_with_diagnostics(
            branch=branch,
            role=role,
            source_format=source_format,
        )
        selected = resolution.parser
        candidates = _matching_registry_rows(
            registry_rows,
            branch=branch,
            role=role,
            source_format=source_format,
        )
        registry_row = selected or (candidates[0] if candidates else None)
        diagnostics = [
            _format_validation_error(validation)
            for validation in resolution.diagnostics
            if not validation.available
        ]
        if registry_row is None:
            diagnostics.append("no parser registry entry")
        elif selected is None:
            validation = validate_parser_registry_row(registry_row)
            if not registry_row.is_active:
                diagnostics.append("parser registry entry is inactive")
            if not validation.available:
                diagnostics.append(_format_validation_error(validation))

        return ParserCoverageRow(
            branch=branch,
            role=role,
            source_format=source_format,
            files_count=files_count,
            parser_active=selected is not None,
            parser_class=registry_row.parser_class if registry_row else None,
            parser_name=registry_row.parser_name if registry_row else None,
            parser_version=registry_row.parser_version if registry_row else None,
            registry_is_active=registry_row.is_active if registry_row else None,
            supported_role=registry_row.supported_role if registry_row else None,
            action=_coverage_action(
                files_count=files_count,
                selected=selected,
                registry_row=registry_row,
                diagnostics=tuple(diagnostics),
            ),
            diagnostics=tuple(dict.fromkeys(diagnostics)),
        )


def run_parser_coverage(
    *,
    branch: str | None = None,
    session: Session | None = None,
    write_reports: bool = True,
) -> ParserCoverageResult:
    """Build parser coverage matrix and optionally persist reports."""
    if session is not None:
        result = ParserCoverageService(session).build(branch=branch)
        return _write_reports(result) if write_reports else result

    with session_scope() as managed_session:
        result = ParserCoverageService(managed_session).build(branch=branch)
    return _write_reports(result) if write_reports else result


def load_stage_one_diagnostics(*, branch: str | None = None) -> dict[str, Any]:
    """Load Stage One sorted-path JSON counts for diagnostics only."""
    diagnostics: dict[str, Any] = {}
    paths = {
        "dns": SORT_PATH_DNS_FILE,
        "host": SORT_PATH_HOST_FILE,
    }
    for current_branch, path in paths.items():
        if branch is not None and current_branch != branch:
            continue
        diagnostics[current_branch] = _stage_one_path_diagnostic(current_branch, path)
    return diagnostics


def coverage_result_payload(result: ParserCoverageResult) -> dict[str, Any]:
    """Return JSON-serializable payload for reports and CLI summaries."""
    return asdict(result)


def _write_reports(result: ParserCoverageResult) -> ParserCoverageResult:
    payload = coverage_result_payload(result)
    report_paths = save_parser_coverage_reports(payload)
    return replace(result, report_paths=report_paths)


def _stage_one_path_diagnostic(branch: str, path_value: str) -> dict[str, Any]:
    path = Path(path_value).expanduser() if path_value else Path()
    if not path_value:
        return {
            "branch": branch,
            "available": False,
            "path": "",
            "error": "config path is empty",
            "counts": [],
            "total_files": 0,
        }
    if not path.exists():
        return {
            "branch": branch,
            "available": False,
            "path": str(path),
            "error": "file does not exist",
            "counts": [],
            "total_files": 0,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "branch": branch,
            "available": False,
            "path": str(path),
            "error": str(exc),
            "counts": [],
            "total_files": 0,
        }

    counts = _stage_one_counts_from_payload(payload)
    return {
        "branch": branch,
        "available": True,
        "path": str(path),
        "counts": counts,
        "total_files": sum(row["files_count"] for row in counts),
    }


def _stage_one_counts_from_payload(payload: Any) -> list[dict[str, Any]]:
    counts: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return counts
    for role, formats in payload.items():
        if not isinstance(formats, dict):
            continue
        for source_format, files in formats.items():
            counts.append(
                {
                    "role": str(role),
                    "source_format": str(source_format),
                    "files_count": _stage_one_file_count(files),
                }
            )
    return sorted(counts, key=lambda row: (_role_sort_value(row["role"]), row["source_format"]))


def _stage_one_file_count(files: Any) -> int:
    if isinstance(files, list):
        return len(files)
    if isinstance(files, dict):
        return len(files)
    return 0


def _matching_registry_rows(
    registry_rows: tuple[ParserRegistry, ...],
    *,
    branch: str,
    role: str,
    source_format: str,
) -> list[ParserRegistry]:
    matches = [
        row
        for row in registry_rows
        if row.branch == branch
        and row.source_format == source_format
        and (row.supported_role is None or row.supported_role == role)
    ]
    return sorted(matches, key=lambda row: (row.priority, row.id or 0))


def _roles_for_registry_row(row: ParserRegistry) -> tuple[str, ...]:
    if row.supported_role is not None:
        return (row.supported_role,)
    return ROLE_VALUES


def _coverage_action(
    *,
    files_count: int,
    selected: ParserRegistry | None,
    registry_row: ParserRegistry | None,
    diagnostics: tuple[str, ...],
) -> str:
    if selected is not None:
        return "ready_for_normalization" if files_count else "parser_available_empty_bucket"
    if registry_row is None:
        return "add_parser_registry_entry"
    validation = validate_parser_registry_row(registry_row)
    if not validation.available:
        return "implement_parser_class"
    if not registry_row.is_active:
        return "activate_parser_registry_entry"
    if diagnostics:
        return "fix_parser_registry_entry"
    return "investigate_parser_resolution"


def _coverage_summary(
    rows: tuple[ParserCoverageRow, ...],
    registry_rows: tuple[ParserRegistry, ...],
) -> dict[str, Any]:
    catalog_rows = [row for row in rows if row.files_count > 0]
    gap_rows = [row for row in catalog_rows if not row.parser_active]
    empty_parser_rows = [row for row in rows if row.files_count == 0 and row.parser_active]
    missing_parser_rows = [
        row
        for row in rows
        if row.action in {
            "add_parser_registry_entry",
            "fix_parser_registry_entry",
            "implement_parser_class",
            "investigate_parser_resolution",
        }
    ]
    action_counts: dict[str, int] = defaultdict(int)
    branch_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        action_counts[row.action] += 1
        branch_counts[row.branch] += 1
    inactive_registry_rows = [row for row in registry_rows if not row.is_active]
    return {
        "matrix_rows": len(rows),
        "catalog_rows": len(catalog_rows),
        "catalog_files": sum(row.files_count for row in rows),
        "catalog_gap_rows": len(gap_rows),
        "missing_parser_rows": len(missing_parser_rows),
        "empty_parser_rows": len(empty_parser_rows),
        "registry_rows": len(registry_rows),
        "inactive_registry_rows": len(inactive_registry_rows),
        "actions": dict(sorted(action_counts.items())),
        "branches": dict(sorted(branch_counts.items())),
    }


def _coverage_key_sort(key: CoverageKey) -> tuple[int, int, str]:
    branch, role, source_format = key
    return (_branch_sort_value(branch), _role_sort_value(role), source_format)


def _branch_sort_value(branch: str) -> int:
    try:
        return BRANCH_VALUES.index(branch)
    except ValueError:
        return len(BRANCH_VALUES)


def _role_sort_value(role: str) -> int:
    try:
        return ROLE_VALUES.index(role)
    except ValueError:
        return len(ROLE_VALUES)


def _validate_branch_filter(branch: str | None) -> None:
    if branch is not None and branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"Unsupported branch filter: {branch}. Allowed values: {allowed}")


def _format_validation_error(validation: Any) -> str:
    return f"{validation.qualified_name}: {validation.error}"
