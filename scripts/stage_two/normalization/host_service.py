"""Host normalization service tying parser runs, Parquet writes, and artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.repositories import ArtifactRepository, DatasetFileRepository, ParserRepository
from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parquet import ParquetArtifactWriter
from scripts.stage_two.parser_registry import ParserResolver
from scripts.stage_two.parsers import ParserContext, ParserResult
from scripts.stage_two.reports import save_parser_run_reports


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
        schema_version = self.resolver.resolve_schema_version(
            parser_metadata,
            branch=dataset_file.branch,
        )

        parser_run = self.parser_repository.create_parser_run(
            file=dataset_file,
            parser_name=parser_metadata.parser_name,
            parser_version=parser_metadata.parser_version,
            parser_registry=parser_metadata,
            schema_version=schema_version,
        )
        try:
            parser_class = self.resolver.load_parser_class(parser_metadata)
            if parser_class is None:
                raise RuntimeError(
                    "parser class unavailable: "
                    f"{parser_metadata.parser_module}.{parser_metadata.parser_class}"
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
            write_result = None
            artifact = None
            parse_batches = getattr(parser, "parse_batches", None)
            if callable(parse_batches):
                result, artifact, output_path, modality = self._parse_and_write_batches(
                    parse_batches,
                    Path(dataset_file.file_path),
                    context,
                    dataset_file=dataset_file,
                    parser_run_id=parser_run.id,
                    schema_version_id=schema_version.id if schema_version is not None else None,
                    schema_name=parser_metadata.normalized_schema_name,
                    schema_version=parser_metadata.normalized_schema_version,
                )
            else:
                result = parser.parse(Path(dataset_file.file_path), context)
                modality = result.events[0]["modality"] if result.events else "host"
                if result.events:
                    write_result = self.writer.write_normalized(
                        result.events,
                        branch=dataset_file.branch,
                        role=dataset_file.role,
                        modality=modality,
                        dataset_slug=dataset_file.dataset.slug,
                        schema_version=parser_metadata.normalized_schema_version,
                        run_id=parser_run.id,
                    )
                output_path = write_result.relative_path if write_result else None
            status_decision = result.status_decision
            status = status_decision.parser_run_status
        except Exception as exc:
            error_message = _exception_message(exc)
            self.parser_repository.fail_parser_run(parser_run, error_message)
            self.file_repository.mark_file_status(dataset_file, "FAILED", error_message=error_message)
            report_paths = save_parser_run_reports(
                parser_run=parser_run,
                dataset_file=dataset_file,
                parser_registry=parser_metadata,
                error_message=error_message,
                storage_root=self.writer.storage_root,
            )
            self.parser_repository.set_parser_run_report_path(
                parser_run,
                report_paths["en_parser_json"],
            )
            return None
        self.parser_repository.finish_parser_run(
            parser_run,
            status=status,
            rows_read=result.rows_read,
            rows_parsed=result.rows_parsed,
            rows_failed=result.rows_failed,
            events_emitted=result.events_emitted,
            output_parquet_path=output_path,
            warning_count=len(result.warnings),
            error_message=_parser_result_error_message(result),
        )
        if write_result is not None:
            artifact = self.writer.register_normalized_artifact(
                self.artifact_repository,
                write_result,
                dataset_id=dataset_file.dataset_id,
                file_id=dataset_file.id,
                parser_run_id=parser_run.id,
                schema_version_id=schema_version.id if schema_version is not None else None,
                role=dataset_file.role,
                branch=dataset_file.branch,
                modality=modality,
                source_format=dataset_file.source_format,
                schema_name=parser_metadata.normalized_schema_name,
                schema_version=parser_metadata.normalized_schema_version,
                event_count=result.events_emitted,
                status=status,
            )
        self.file_repository.mark_file_status(
            dataset_file,
            status_decision.file_status,
            error_message=status_decision.reason if status_decision.file_status == "FAILED" else None,
        )
        report_paths = save_parser_run_reports(
            parser_run=parser_run,
            dataset_file=dataset_file,
            parser_result=result,
            parser_registry=parser_metadata,
            output_artifact_path=output_path,
            storage_root=self.writer.storage_root,
        )
        self.parser_repository.set_parser_run_report_path(
            parser_run,
            report_paths["en_parser_json"],
        )
        return artifact

    def _parse_and_write_batches(
        self,
        parse_batches: Any,
        path: Path,
        context: ParserContext,
        *,
        dataset_file: DatasetFile,
        parser_run_id: int,
        schema_version_id: int | None,
        schema_name: str,
        schema_version: str,
    ) -> tuple[ParserResult, NormalizedArtifact | None, str | None, str]:
        rows_read = 0
        rows_parsed = 0
        rows_failed = 0
        events_emitted = 0
        warnings: list[str] = []
        error_samples: list[str] = []
        bytes_read: int | None = None
        artifact: NormalizedArtifact | None = None
        output_paths: list[str] = []
        first_modality = "host"

        for batch_index, batch_result in enumerate(parse_batches(path, context), start=1):
            rows_read += batch_result.rows_read
            rows_parsed += batch_result.rows_parsed
            rows_failed += batch_result.rows_failed
            events_emitted += batch_result.events_emitted
            warnings.extend(batch_result.warnings)
            error_samples.extend(batch_result.error_samples)
            bytes_read = batch_result.bytes_read
            if not batch_result.events:
                continue
            batch_modality = batch_result.events[0]["modality"]
            first_modality = batch_modality if first_modality == "host" else first_modality
            write_result = self.writer.write_normalized(
                batch_result.events,
                branch=dataset_file.branch,
                role=dataset_file.role,
                modality=batch_modality,
                dataset_slug=dataset_file.dataset.slug,
                schema_version=schema_version,
                run_id=f"{parser_run_id}-{batch_index:06d}",
            )
            output_paths.append(write_result.relative_path)
            registered = self.writer.register_normalized_artifact(
                self.artifact_repository,
                write_result,
                dataset_id=dataset_file.dataset_id,
                file_id=dataset_file.id,
                parser_run_id=parser_run_id,
                schema_version_id=schema_version_id,
                role=dataset_file.role,
                branch=dataset_file.branch,
                modality=batch_modality,
                source_format=dataset_file.source_format,
                schema_name=schema_name,
                schema_version=schema_version,
                event_count=batch_result.events_emitted,
                status=batch_result.status_decision.parser_run_status,
            )
            artifact = artifact or registered

        return (
            ParserResult(
                rows_read=rows_read,
                rows_parsed=rows_parsed,
                rows_failed=rows_failed,
                events=[],
                warnings=warnings,
                bytes_read=bytes_read,
                error_samples=error_samples,
                emitted_events_count=events_emitted,
            ),
            artifact,
            _batched_output_path(output_paths, parser_run_id),
            first_modality,
        )


def _parser_result_error_message(result: ParserResult) -> str | None:
    decision = result.status_decision
    if decision.parser_run_status not in {"FAILED", "PARTIAL_SUCCESS"}:
        return None
    if result.error_samples:
        samples = "; ".join(result.error_samples[:3])
        return f"{decision.reason}: {samples}"
    return decision.reason


def _batched_output_path(output_paths: list[str], parser_run_id: int) -> str | None:
    if not output_paths:
        return None
    if len(output_paths) == 1:
        return output_paths[0]
    first = Path(output_paths[0])
    return (first.parent / f"part-{parser_run_id}-*.parquet").as_posix()


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__
