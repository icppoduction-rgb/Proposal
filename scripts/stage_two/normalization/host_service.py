"""Host normalization service tying parser runs, Parquet writes, and artifacts."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.repositories import ArtifactRepository, DatasetFileRepository, ParserRepository
from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parquet import ParquetArtifactWriter
from scripts.stage_two.parser_registry import ParserResolver
from scripts.stage_two.parsers import ParserContext
from scripts.stage_two.parsers.bson import HostBsonSandboxParser
from scripts.stage_two.parsers.host import (
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostNetflowParser,
    HostSyscallTraceParser,
)
from scripts.stage_two.parsers.packet import HostPacketCaptureParser


HOST_PARSER_CLASSES = {
    "HostBsonSandboxParser": HostBsonSandboxParser,
    "HostCsvParser": HostCsvParser,
    "HostJsonLinesParser": HostJsonLinesParser,
    "HostLineLogParser": HostLineLogParser,
    "HostNetflowParser": HostNetflowParser,
    "HostPacketCaptureParser": HostPacketCaptureParser,
    "HostSyscallTraceParser": HostSyscallTraceParser,
}


class HostNormalizationService:
    """Normalize Host files and register normalized Parquet artifacts."""

    def __init__(
        self,
        session: Session,
        *,
        writer: ParquetArtifactWriter | None = None,
    ) -> None:
        """Initialize the service with an externally managed session."""
        self.session = session
        self.writer = writer or ParquetArtifactWriter()
        self.resolver = ParserResolver(session)
        self.parser_repository = ParserRepository(session)
        self.file_repository = DatasetFileRepository(session)
        self.artifact_repository = ArtifactRepository(session)

    def normalize_file(self, dataset_file: DatasetFile) -> NormalizedArtifact | None:
        """Normalize one Host file, write Parquet, and register the artifact."""
        parser_metadata = self.resolver.resolve_or_mark_unsupported(dataset_file)
        if parser_metadata is None:
            return None
        parser_class = HOST_PARSER_CLASSES.get(parser_metadata.parser_class)
        if parser_class is None:
            self.file_repository.mark_file_status(dataset_file, "SKIPPED")
            return None

        parser_run = self.parser_repository.create_parser_run(
            file=dataset_file,
            parser_name=parser_metadata.parser_name,
            parser_version=parser_metadata.parser_version,
            parser_registry=parser_metadata,
        )
        parser = parser_class(label_resolver=LabelResolver(session=self.session))
        context = ParserContext(
            dataset_id=dataset_file.dataset_id,
            file_id=dataset_file.id,
            dataset_name=dataset_file.dataset.name,
            dataset_role=dataset_file.role,
            branch=dataset_file.branch,
            source_format=dataset_file.source_format,
            source_file_path=dataset_file.relative_path or dataset_file.file_path,
            source_file_hash=dataset_file.file_hash_sha256,
            parser_run_id=parser_run.id,
            metadata=dataset_file.metadata_json or {},
        )
        try:
            result = parser.parse(Path(dataset_file.file_path), context)
            status = "PARTIAL_SUCCESS" if result.has_failures else "SUCCESS"
            modality = result.events[0]["modality"] if result.events else "host"
            write_result = self.writer.write_normalized(
                result.events,
                branch=dataset_file.branch,
                role=dataset_file.role,
                modality=modality,
                dataset_slug=dataset_file.dataset.slug,
                schema_version=parser_metadata.normalized_schema_version,
                run_id=parser_run.id,
            )
        except Exception as exc:
            error_message = str(exc)
            self.parser_repository.fail_parser_run(parser_run, error_message)
            self.file_repository.mark_file_status(dataset_file, "FAILED", error_message=error_message)
            return None
        self.parser_repository.finish_parser_run(
            parser_run,
            status=status,
            rows_read=result.rows_read,
            rows_parsed=result.rows_parsed,
            rows_failed=result.rows_failed,
            events_emitted=result.events_emitted,
            output_parquet_path=write_result.relative_path,
            warning_count=len(result.warnings),
        )
        artifact = self.writer.register_normalized_artifact(
            self.artifact_repository,
            write_result,
            dataset_id=dataset_file.dataset_id,
            file_id=dataset_file.id,
            parser_run_id=parser_run.id,
            schema_version_id=None,
            role=dataset_file.role,
            branch=dataset_file.branch,
            modality=modality,
            source_format=dataset_file.source_format,
            schema_name=parser_metadata.normalized_schema_name,
            schema_version=parser_metadata.normalized_schema_version,
            event_count=result.events_emitted,
            status=status,
        )
        file_status = "PARTIALLY_PARSED" if result.has_failures else "PARSED"
        self.file_repository.mark_file_status(dataset_file, file_status)
        return artifact
