"""Operational status transition helpers for Stage Two catalog files."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import PATH_DATA_STORAGE, REPORTS_EN_STAGE_TWO, REPORTS_RU_STAGE_TWO
from scripts.db.models import Dataset, DatasetFile
from scripts.db.models.constants import (
    ACTIVE_CATALOG_SOURCE_GROUP,
    ACTIVE_DATASET_ROLE_VALUES,
    BRANCH_VALUES,
)
from scripts.stage_two.parser_registry.resolver import ParserResolver
from scripts.stage_two.parser_registry.seed import ParserClassValidationResult


READY_FOR_PARSING_STATUS = "READY_FOR_PARSING"
MARK_READY_ALLOWED_STATUSES: tuple[str, ...] = ("REGISTERED", "CHANGED", "DISCOVERED")
MARK_READY_RETRY_STATUSES: tuple[str, ...] = ("FAILED", "SKIPPED", "PARTIALLY_PARSED")
MARK_READY_BLOCKED_STATUSES: tuple[str, ...] = (
    "EMPTY_FILE",
    "FAILED",
    "PARSED",
    "PARTIALLY_PARSED",
    "SKIPPED",
)
ProgressCallback = Callable[[str, dict[str, Any]], None]
MARK_READY_SKIPPED_STATUSES: tuple[str, ...] = (
    *MARK_READY_BLOCKED_STATUSES,
    "READY_FOR_PARSING",
    "UNSUPPORTED_FORMAT",
)


@dataclass(frozen=True)
class MarkReadyRequest:
    """Filters and execution mode for a mark-ready operation."""

    branch: str
    role: str
    source_format: str
    apply_changes: bool = False
    retry_failed: bool = False
    file_ids: tuple[int, ...] | None = None


@dataclass(frozen=True)
class MarkReadyDiagnostic:
    """Parser availability diagnostic exposed in mark-ready reports."""

    parser_module: str | None
    parser_class: str | None
    available: bool
    error: str | None = None


@dataclass(frozen=True)
class MarkReadyCandidate:
    """One file considered by mark-ready."""

    file_id: int | None
    file_path: str
    previous_status: str
    next_status: str | None
    eligible: bool


@dataclass(frozen=True)
class MarkReadyResult:
    """Count report for a mark-ready operation."""

    status: str
    branch: str
    role: str
    source_format: str
    dry_run: bool
    retry_failed: bool
    selected: int
    eligible: int
    updated: int
    skipped_by_status: dict[str, int]
    unsupported: int
    empty: int
    errors: int
    parser_name: str | None = None
    parser_class: str | None = None
    candidates: tuple[MarkReadyCandidate, ...] = ()
    diagnostics: tuple[MarkReadyDiagnostic, ...] = ()
    report_paths: dict[str, str] | None = None


class MarkReadyService:
    """Safely promote catalog files to READY_FOR_PARSING without committing."""

    def __init__(
        self,
        session: Session,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize the service with an externally managed session."""
        self.session = session
        self.resolver = ParserResolver(session)
        self.progress_callback = progress_callback

    def mark_ready(self, request: MarkReadyRequest) -> MarkReadyResult:
        """Return count report and optionally update eligible catalog rows."""
        _validate_request(request)
        files = self._selected_files(request)
        resolution = self.resolver.resolve_with_diagnostics(
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
        )
        parser = resolution.parser
        skipped_by_status, empty, errors = _status_counts(files)
        if parser is None:
            return MarkReadyResult(
                status="UNSUPPORTED_FORMAT",
                branch=request.branch,
                role=request.role,
                source_format=request.source_format,
                dry_run=not request.apply_changes,
                retry_failed=request.retry_failed,
                selected=len(files),
                eligible=0,
                updated=0,
                skipped_by_status=dict(sorted(skipped_by_status.items())),
                unsupported=len(files),
                empty=empty,
                errors=errors,
                candidates=_candidate_rows(files, eligible_statuses=()),
                diagnostics=_parser_diagnostics(resolution.diagnostics),
            )

        eligible_statuses = (
            MARK_READY_RETRY_STATUSES if request.retry_failed else MARK_READY_ALLOWED_STATUSES
        )
        eligible_files = [file for file in files if file.status in eligible_statuses]
        candidates = _candidate_rows(files, eligible_statuses=eligible_statuses)
        updated = 0
        if request.apply_changes and eligible_files:
            now = datetime.now(timezone.utc)
            total = len(eligible_files)
            for index, file in enumerate(eligible_files, start=1):
                previous_status = file.status
                file.status = READY_FOR_PARSING_STATUS
                file.error_message = None
                file.last_seen_at = now
                file.updated_at = now
                updated += 1
                self._emit(
                    "file_marked_ready",
                    current=index,
                    total=total,
                    file_id=file.id,
                    file_path=file.file_path,
                    previous_status=previous_status,
                )
            self.session.flush()
        elif not request.apply_changes:
            total = len(files)
            for index, file in enumerate(files, start=1):
                self._emit(
                    "file_seen",
                    current=index,
                    total=total,
                    file_id=file.id,
                    file_path=file.file_path,
                    status=file.status,
                )

        return MarkReadyResult(
            status="DRY_RUN" if not request.apply_changes else "SUCCESS",
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
            dry_run=not request.apply_changes,
            retry_failed=request.retry_failed,
            selected=len(files),
            eligible=len(eligible_files),
            updated=updated,
            skipped_by_status=dict(sorted(skipped_by_status.items())),
            unsupported=0,
            empty=empty,
            errors=errors,
            parser_name=parser.parser_name,
            parser_class=parser.parser_class,
            candidates=candidates,
            diagnostics=_parser_diagnostics(resolution.diagnostics),
        )

    def _selected_files(self, request: MarkReadyRequest) -> list[DatasetFile]:
        statement = (
            select(DatasetFile)
            .where(
                DatasetFile.branch == request.branch,
                DatasetFile.role == request.role,
                DatasetFile.source_format == request.source_format,
            )
            .order_by(DatasetFile.id.asc())
        )
        if request.file_ids is not None:
            statement = statement.where(DatasetFile.id.in_(request.file_ids))
        else:
            statement = statement.join(Dataset).where(
                Dataset.source_group == ACTIVE_CATALOG_SOURCE_GROUP
            )
        return list(self.session.execute(statement).scalars().all())

    def _emit(self, event: str, **payload: Any) -> None:
        if self.progress_callback is not None:
            self.progress_callback(event, payload)


def _validate_request(request: MarkReadyRequest) -> None:
    if request.branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"mark-ready branch must be one of: {allowed}")
    if request.role not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"mark-ready role must be one of: {allowed}")
    if not request.source_format.strip():
        raise ValueError("mark-ready format must not be empty")


def _candidate_rows(
    files: list[DatasetFile],
    *,
    eligible_statuses: tuple[str, ...],
) -> tuple[MarkReadyCandidate, ...]:
    eligible = set(eligible_statuses)
    return tuple(
        MarkReadyCandidate(
            file_id=file.id,
            file_path=file.file_path,
            previous_status=file.status or "<NULL>",
            next_status=READY_FOR_PARSING_STATUS if file.status in eligible else None,
            eligible=file.status in eligible,
        )
        for file in files
    )


def _status_counts(files: list[DatasetFile]) -> tuple[Counter[str], int, int]:
    skipped_by_status: Counter[str] = Counter()
    empty = 0
    errors = 0
    known_skipped = set(MARK_READY_SKIPPED_STATUSES)
    for file in files:
        status = file.status or "<NULL>"
        if status == "EMPTY_FILE":
            empty += 1
        if status in MARK_READY_ALLOWED_STATUSES:
            continue
        skipped_by_status[status] += 1
        if status not in known_skipped:
            errors += 1
    return skipped_by_status, empty, errors


def _parser_diagnostics(
    diagnostics: tuple[ParserClassValidationResult, ...],
) -> tuple[MarkReadyDiagnostic, ...]:
    return tuple(
        MarkReadyDiagnostic(
            parser_module=diagnostic.parser_module,
            parser_class=diagnostic.parser_class,
            available=diagnostic.available,
            error=diagnostic.error,
        )
        for diagnostic in diagnostics
    )


def save_mark_ready_reports(result: MarkReadyResult) -> MarkReadyResult:
    """Persist EN/RU mark-ready reports and return a result with report paths."""
    if not PATH_DATA_STORAGE.strip():
        return result
    storage_root = Path(PATH_DATA_STORAGE).expanduser()
    mode = "retry_failed" if result.retry_failed else "initial"
    stem = _report_stem(result, mode=mode)
    paths = {
        "en_json": f"{REPORTS_EN_STAGE_TWO}/status/{stem}.json",
        "en_md": f"{REPORTS_EN_STAGE_TWO}/status/{stem}.md",
        "ru_json": f"{REPORTS_RU_STAGE_TWO}/status/{stem}.json",
        "ru_md": f"{REPORTS_RU_STAGE_TWO}/status/{stem}.md",
    }
    payload = _result_payload(result, report_paths=paths)
    for key, relative_path in paths.items():
        path = storage_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if key.endswith("_json"):
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        else:
            language = "ru" if key.startswith("ru") else "en"
            path.write_text(_render_report_markdown(payload, language=language), encoding="utf-8")
    return replace(result, report_paths=paths)


def _result_payload(result: MarkReadyResult, *, report_paths: dict[str, str]) -> dict[str, Any]:
    return {
        "status": result.status,
        "branch": result.branch,
        "role": result.role,
        "source_format": result.source_format,
        "dry_run": result.dry_run,
        "retry_failed": result.retry_failed,
        "selected": result.selected,
        "eligible": result.eligible,
        "updated": result.updated,
        "skipped_by_status": result.skipped_by_status,
        "unsupported": result.unsupported,
        "empty": result.empty,
        "errors": result.errors,
        "parser_name": result.parser_name,
        "parser_class": result.parser_class,
        "candidates": [candidate.__dict__ for candidate in result.candidates],
        "diagnostics": [diagnostic.__dict__ for diagnostic in result.diagnostics],
        "report_paths": report_paths,
    }


def _report_stem(result: MarkReadyResult, *, mode: str) -> str:
    source_format = re.sub(r"[^a-zA-Z0-9_.-]+", "-", result.source_format).strip("-")
    return f"mark_ready_{result.branch}_{result.role}_{source_format}_{mode}".lower()


def _render_report_markdown(payload: dict[str, Any], *, language: str) -> str:
    if language == "ru":
        title = "Stage Two mark-ready report"
        summary = "Summary"
    else:
        title = "Stage Two mark-ready report"
        summary = "Summary"
    candidate_lines = [
        (
            f"- `{candidate['previous_status']}` -> "
            f"`{candidate['next_status'] or '-'}`: `{candidate['file_path']}`"
        )
        for candidate in payload["candidates"]
    ]
    return (
        f"# {title}\n\n"
        f"## {summary}\n\n"
        f"- Status: `{payload['status']}`\n"
        f"- Branch: `{payload['branch']}`\n"
        f"- Role: `{payload['role']}`\n"
        f"- Format: `{payload['source_format']}`\n"
        f"- Dry run: `{payload['dry_run']}`\n"
        f"- Selected: `{payload['selected']}`\n"
        f"- Eligible: `{payload['eligible']}`\n"
        f"- Updated: `{payload['updated']}`\n\n"
        "## Files\n\n"
        f"{chr(10).join(candidate_lines) if candidate_lines else '- No files matched.'}\n"
    )
