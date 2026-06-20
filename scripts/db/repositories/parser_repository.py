"""Repository for parser registry and parser run lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from scripts.db.models import DatasetFile, ParserRegistry, ParserRun, SchemaVersion
from scripts.db.repositories.base_repository import BaseRepository


class ParserRepository(BaseRepository[ParserRegistry]):
    """Data access methods for parser routing and parser runs."""

    model = ParserRegistry

    def resolve_parser(
        self,
        *,
        branch: str,
        role: str,
        source_format: str,
    ) -> ParserRegistry | None:
        """Resolve the highest priority active parser for branch/role/source_format."""
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
            .limit(1)
        )
        return self.session.execute(statement).scalar_one_or_none()

    def create_parser_run(
        self,
        *,
        file: DatasetFile,
        parser_name: str,
        parser_version: str,
        parser_registry: ParserRegistry | None = None,
        schema_version: SchemaVersion | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ParserRun:
        """Create a RUNNING parser run for a registered raw file."""
        run = ParserRun(
            run_uid=uuid4(),
            file=file,
            parser_registry=parser_registry,
            parser_name=parser_name,
            parser_version=parser_version,
            schema_version=schema_version,
            status="RUNNING",
            metadata_json=metadata_json,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get_latest_resumable_parser_run(
        self,
        *,
        file: DatasetFile,
        parser_name: str,
        parser_version: str,
        schema_version: SchemaVersion | None = None,
    ) -> ParserRun | None:
        """Return the latest non-success parser run that can be resumed."""
        statement = (
            select(ParserRun)
            .where(
                ParserRun.file_id == file.id,
                ParserRun.parser_name == parser_name,
                ParserRun.parser_version == parser_version,
                ParserRun.status.in_(("RUNNING", "FAILED", "PARTIAL_SUCCESS")),
            )
            .order_by(ParserRun.id.desc())
            .limit(1)
        )
        if schema_version is not None:
            statement = statement.where(ParserRun.schema_version_id == schema_version.id)
        return self.session.execute(statement).scalar_one_or_none()

    def resume_parser_run(self, run: ParserRun, metadata_json: dict[str, Any] | None = None) -> ParserRun:
        """Mark an existing parser run as RUNNING before appending missing parts."""
        run.status = "RUNNING"
        run.finished_at = None
        run.error_message = None
        if metadata_json is not None:
            current_metadata = dict(run.metadata_json or {})
            current_metadata.update(metadata_json)
            run.metadata_json = current_metadata
        self.session.flush()
        return run

    def finish_parser_run(
        self,
        run: ParserRun,
        *,
        status: str = "SUCCESS",
        rows_read: int | None = None,
        rows_parsed: int | None = None,
        rows_failed: int | None = None,
        events_emitted: int | None = None,
        output_parquet_path: str | None = None,
        warning_count: int | None = None,
        error_message: str | None = None,
        report_path: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ParserRun:
        """Mark a parser run as finished without committing."""
        run.status = status
        run.finished_at = datetime.now(timezone.utc)
        run.rows_read = rows_read
        run.rows_parsed = rows_parsed
        run.rows_failed = rows_failed
        run.events_emitted = events_emitted
        run.output_parquet_path = output_parquet_path
        if warning_count is not None:
            run.warning_count = warning_count
        run.error_message = error_message
        run.report_path = report_path
        if metadata_json is not None:
            current_metadata = dict(run.metadata_json or {})
            current_metadata.update(metadata_json)
            run.metadata_json = current_metadata
        self.session.flush()
        return run

    def fail_parser_run(self, run: ParserRun, error_message: str) -> ParserRun:
        """Mark a parser run as FAILED."""
        run.status = "FAILED"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = error_message
        self.session.flush()
        return run

    def set_parser_run_report_path(self, run: ParserRun, report_path: str) -> ParserRun:
        """Attach a diagnostic report path to an existing parser run."""
        run.report_path = report_path
        self.session.flush()
        return run
