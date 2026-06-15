"""Parser registry resolver for Stage Two raw files."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, ParserRegistry
from scripts.db.repositories import DatasetFileRepository, ParserRepository
from scripts.stage_two.parser_registry.seed import ParserClassValidationResult, validate_parser_registry_row


@dataclass(frozen=True)
class ParserResolutionResult:
    """Parser resolution result with class availability diagnostics."""

    parser: ParserRegistry | None
    diagnostics: tuple[ParserClassValidationResult, ...]


class ParserResolver:
    """Resolve parser metadata by branch, role, and source format."""

    def __init__(self, session: Session) -> None:
        """Initialize the resolver with an externally managed session."""
        self.session = session
        self.parser_repository = ParserRepository(session)
        self.file_repository = DatasetFileRepository(session)

    def resolve(self, *, branch: str, role: str, source_format: str) -> ParserRegistry | None:
        """Return matching parser metadata or None when unsupported."""
        return self.resolve_with_diagnostics(
            branch=branch,
            role=role,
            source_format=source_format,
        ).parser

    def resolve_with_diagnostics(
        self,
        *,
        branch: str,
        role: str,
        source_format: str,
    ) -> ParserResolutionResult:
        """Return the first valid active parser and diagnostics for skipped candidates."""
        diagnostics: list[ParserClassValidationResult] = []
        for parser_metadata in self._active_candidates(
            branch=branch,
            role=role,
            source_format=source_format,
        ):
            validation = validate_parser_registry_row(parser_metadata)
            diagnostics.append(validation)
            if validation.available:
                return ParserResolutionResult(
                    parser=parser_metadata,
                    diagnostics=tuple(diagnostics),
                )
        return ParserResolutionResult(parser=None, diagnostics=tuple(diagnostics))

    def resolve_for_file(self, dataset_file: DatasetFile) -> ParserRegistry | None:
        """Return parser metadata for a registered dataset file."""
        return self.resolve(
            branch=dataset_file.branch,
            role=dataset_file.role,
            source_format=dataset_file.source_format,
        )

    def resolve_or_mark_unsupported(self, dataset_file: DatasetFile) -> ParserRegistry | None:
        """Resolve a parser or mark the file UNSUPPORTED_FORMAT without committing."""
        parser = self.resolve_for_file(dataset_file)
        if parser is None:
            self.file_repository.mark_file_status(dataset_file, "UNSUPPORTED_FORMAT")
        return parser

    def validate_active_registry(self) -> tuple[ParserClassValidationResult, ...]:
        """Validate all active registry rows for coverage diagnostics."""
        statement = (
            select(ParserRegistry)
            .where(ParserRegistry.is_active.is_(True))
            .order_by(
                ParserRegistry.branch.asc(),
                ParserRegistry.source_format.asc(),
                ParserRegistry.supported_role.asc().nullsfirst(),
                ParserRegistry.priority.asc(),
                ParserRegistry.id.asc(),
            )
        )
        rows = self.session.execute(statement).scalars().all()
        return tuple(validate_parser_registry_row(row) for row in rows)

    def _active_candidates(
        self,
        *,
        branch: str,
        role: str,
        source_format: str,
    ) -> list[ParserRegistry]:
        statement = (
            select(ParserRegistry)
            .where(
                ParserRegistry.branch == branch,
                ParserRegistry.source_format == source_format,
                ParserRegistry.is_active.is_(True),
                (
                    (ParserRegistry.supported_role == role)
                    | (ParserRegistry.supported_role.is_(None))
                ),
            )
            .order_by(ParserRegistry.priority.asc(), ParserRegistry.id.asc())
        )
        return list(self.session.execute(statement).scalars().all())
