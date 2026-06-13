"""Parser registry resolver for Stage Two raw files."""

from __future__ import annotations

from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, ParserRegistry
from scripts.db.repositories import DatasetFileRepository, ParserRepository


class ParserResolver:
    """Resolve parser metadata by branch, role, and source format."""

    def __init__(self, session: Session) -> None:
        """Initialize the resolver with an externally managed session."""
        self.session = session
        self.parser_repository = ParserRepository(session)
        self.file_repository = DatasetFileRepository(session)

    def resolve(self, *, branch: str, role: str, source_format: str) -> ParserRegistry | None:
        """Return matching parser metadata or None when unsupported."""
        return self.parser_repository.resolve_parser(
            branch=branch,
            role=role,
            source_format=source_format,
        )

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
