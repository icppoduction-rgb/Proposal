"""Operational status transition helpers for Stage Two catalog files."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile
from scripts.db.models.constants import BRANCH_VALUES, ROLE_VALUES
from scripts.stage_two.parser_registry.resolver import ParserResolver
from scripts.stage_two.parser_registry.seed import ParserClassValidationResult


READY_FOR_PARSING_STATUS = "READY_FOR_PARSING"
MARK_READY_ALLOWED_STATUSES: tuple[str, ...] = ("REGISTERED", "CHANGED", "DISCOVERED")
MARK_READY_BLOCKED_STATUSES: tuple[str, ...] = (
    "EMPTY_FILE",
    "FAILED",
    "PARSED",
    "PARTIALLY_PARSED",
    "SKIPPED",
)
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
    file_ids: tuple[int, ...] | None = None


@dataclass(frozen=True)
class MarkReadyDiagnostic:
    """Parser availability diagnostic exposed in mark-ready reports."""

    parser_module: str | None
    parser_class: str | None
    available: bool
    error: str | None = None


@dataclass(frozen=True)
class MarkReadyResult:
    """Count report for a mark-ready operation."""

    status: str
    branch: str
    role: str
    source_format: str
    dry_run: bool
    selected: int
    eligible: int
    updated: int
    skipped_by_status: dict[str, int]
    unsupported: int
    empty: int
    errors: int
    parser_name: str | None = None
    parser_class: str | None = None
    diagnostics: tuple[MarkReadyDiagnostic, ...] = ()


class MarkReadyService:
    """Safely promote catalog files to READY_FOR_PARSING without committing."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with an externally managed session."""
        self.session = session
        self.resolver = ParserResolver(session)

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
                selected=len(files),
                eligible=0,
                updated=0,
                skipped_by_status=dict(sorted(skipped_by_status.items())),
                unsupported=len(files),
                empty=empty,
                errors=errors,
                diagnostics=_parser_diagnostics(resolution.diagnostics),
            )

        eligible_files = [file for file in files if file.status in MARK_READY_ALLOWED_STATUSES]
        updated = 0
        if request.apply_changes and eligible_files:
            now = datetime.now(timezone.utc)
            for file in eligible_files:
                file.status = READY_FOR_PARSING_STATUS
                file.error_message = None
                file.last_seen_at = now
                file.updated_at = now
                updated += 1
            self.session.flush()

        return MarkReadyResult(
            status="DRY_RUN" if not request.apply_changes else "SUCCESS",
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
            dry_run=not request.apply_changes,
            selected=len(files),
            eligible=len(eligible_files),
            updated=updated,
            skipped_by_status=dict(sorted(skipped_by_status.items())),
            unsupported=0,
            empty=empty,
            errors=errors,
            parser_name=parser.parser_name,
            parser_class=parser.parser_class,
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
        return list(self.session.execute(statement).scalars().all())


def _validate_request(request: MarkReadyRequest) -> None:
    if request.branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"mark-ready branch must be one of: {allowed}")
    if request.role not in ROLE_VALUES:
        allowed = ", ".join(ROLE_VALUES)
        raise ValueError(f"mark-ready role must be one of: {allowed}")
    if not request.source_format.strip():
        raise ValueError("mark-ready format must not be empty")


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
