"""Parser registry resolver for Stage Two raw files."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, ParserRegistry, SchemaVersion
from scripts.db.repositories import DatasetFileRepository, ParserRepository
from scripts.stage_two.parser_registry.seed import ParserClassValidationResult, validate_parser_registry_row

if TYPE_CHECKING:
    from scripts.stage_two.parsers.base import BaseParser


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

    def load_parser_class(self, parser_metadata: ParserRegistry) -> type["BaseParser"] | None:
        """Load the parser class referenced by an already resolved registry row."""
        validation = validate_parser_registry_row(parser_metadata)
        if not validation.available:
            return None

        from scripts.stage_two.parsers.base import BaseParser

        module = importlib.import_module(parser_metadata.parser_module)
        parser_class = getattr(module, parser_metadata.parser_class)
        if not isinstance(parser_class, type) or not issubclass(parser_class, BaseParser):
            return None
        return parser_class

    def resolve_schema_version(
        self,
        parser_metadata: ParserRegistry,
        *,
        branch: str | None = None,
    ) -> SchemaVersion | None:
        """Return the active normalized schema version used by a parser registry row."""
        if branch is not None:
            branch_schema = self._find_schema_version(parser_metadata, branch=branch)
            if branch_schema is not None:
                return branch_schema
        return self._find_schema_version(parser_metadata, branch=None)

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

    def _find_schema_version(
        self,
        parser_metadata: ParserRegistry,
        *,
        branch: str | None,
    ) -> SchemaVersion | None:
        statement = select(SchemaVersion).where(
            SchemaVersion.schema_name == parser_metadata.normalized_schema_name,
            SchemaVersion.schema_version == parser_metadata.normalized_schema_version,
            SchemaVersion.layer == "normalized",
            SchemaVersion.branch.is_(branch) if branch is None else SchemaVersion.branch == branch,
            SchemaVersion.is_active.is_(True),
        )
        return self.session.execute(statement).scalar_one_or_none()
