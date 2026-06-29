"""Host normalization service tying parser runs, Parquet writes, and artifacts."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.repositories import ArtifactRepository, DatasetFileRepository, ParserRepository
from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.normalization.options import NormalizationOptions, batch_size_for_source_format
from scripts.stage_two.normalization.performance import MemoryTracker, NormalizationPerformance, PerfTimer
from scripts.stage_two.parquet import ParquetArtifactWriter
from scripts.stage_two.parquet.writer import ParquetWriteResult
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
        options: NormalizationOptions | None = None,
    ) -> None:
        """Initialize the service with an externally managed session."""
        self.session = session
        self.options = options or NormalizationOptions()
        self.writer = writer or ParquetArtifactWriter(hash_outputs=self.options.hash_outputs)
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

        run_metadata = {"normalization_options": _options_payload(self.options)}
        parser_run = None
        if self.options.resume:
            parser_run = self.parser_repository.get_latest_resumable_parser_run(
                file=dataset_file,
                parser_name=parser_metadata.parser_name,
                parser_version=parser_metadata.parser_version,
                schema_version=schema_version,
            )
        if parser_run is None:
            parser_run = self.parser_repository.create_parser_run(
                file=dataset_file,
                parser_name=parser_metadata.parser_name,
                parser_version=parser_metadata.parser_version,
                parser_registry=parser_metadata,
                schema_version=schema_version,
                metadata_json=run_metadata,
            )
        else:
            self.parser_repository.resume_parser_run(
                parser_run,
                metadata_json={**run_metadata, "resumed": True},
            )
        performance = NormalizationPerformance(input_size_bytes=dataset_file.file_size_bytes)
        started_at = time.perf_counter()
        memory_tracker = MemoryTracker()
        try:
            with memory_tracker:
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
                result, artifact, output_path, modality = self._parse_and_write_batches(
                    parser.parse_batches,
                    Path(dataset_file.file_path),
                    context,
                    dataset_file=dataset_file,
                    parser_run_id=parser_run.id,
                    schema_version_id=schema_version.id if schema_version is not None else None,
                    schema_name=parser_metadata.normalized_schema_name,
                    schema_version=parser_metadata.normalized_schema_version,
                    performance=performance,
                )
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
        performance.total_seconds = time.perf_counter() - started_at
        performance.peak_memory_bytes = memory_tracker.peak_bytes
        performance.rows_read = result.rows_read
        performance.events_emitted = result.events_emitted
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
            metadata_json={
                "performance": performance.payload(),
                "output_counters": _aggregate_output_counters(dataset_file, result, performance),
            },
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
        performance: NormalizationPerformance,
    ) -> tuple[ParserResult, NormalizedArtifact | None, str | None, str]:
        rows_read = 0
        rows_parsed = 0
        rows_failed = 0
        events_emitted = 0
        warnings: list[str] = []
        error_samples: list[str] = []
        bytes_read: int | None = None
        existing_parts = _existing_parts_by_index(
            self.artifact_repository.get_normalized_artifacts_for_run(parser_run_id)
        ) if self.options.resume else {}
        artifact: NormalizedArtifact | None = next(iter(existing_parts.values()), None)
        output_paths: list[str] = [
            existing_parts[index].normalized_path for index in sorted(existing_parts)
        ]
        first_modality = "host"
        logical_part_index = 0

        batch_iterator = iter(
            parse_batches(
                path,
                context,
                batch_size=batch_size_for_source_format(dataset_file.source_format, self.options),
                packet_mode=self.options.packet_mode,
                sample_size=self.options.sample_size,
            )
        )
        batch_index = 0
        while True:
            with PerfTimer(performance, "parse_seconds"):
                try:
                    batch_result = next(batch_iterator)
                except StopIteration:
                    break
            batch_index += 1
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
            for part_offset, events_part in enumerate(
                _chunk_events(batch_result.events, self.options.max_output_part_rows),
                start=1,
            ):
                logical_part_index += 1
                if logical_part_index in existing_parts:
                    continue
                part_index = logical_part_index
                with PerfTimer(performance, "parquet_write_seconds"):
                    write_result = self.writer.write_normalized(
                        events_part,
                        branch=dataset_file.branch,
                        role=dataset_file.role,
                        modality=batch_modality,
                        dataset_slug=dataset_file.dataset.slug,
                        schema_version=schema_version,
                        run_id=f"{parser_run_id}-{part_index:06d}",
                    )
                output_paths.append(write_result.relative_path)
                with PerfTimer(performance, "catalog_seconds"):
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
                        event_count=len(events_part),
                        status=batch_result.status_decision.parser_run_status,
                        metadata_json={
                            "parser_run_id": parser_run_id,
                            "batch_index": batch_index,
                            "batch_part_index": part_offset,
                            "part_index": part_index,
                            "rows_in_part": len(events_part),
                            "checkpoint": {
                                "rows_read": rows_read,
                                "rows_parsed": rows_parsed,
                                "bytes_read": bytes_read,
                            },
                            "output_counters": _artifact_output_counters(
                                dataset_file,
                                batch_result,
                                write_result,
                                output_rows=len(events_part),
                            ),
                        },
                    )
                artifact = artifact or registered
                performance.output_parts_count += 1

        performance.output_parts_count = len(output_paths)
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


def _chunk_events(events: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    return [events[index : index + chunk_size] for index in range(0, len(events), chunk_size)]


def _existing_parts_by_index(
    artifacts: list[NormalizedArtifact],
) -> dict[int, NormalizedArtifact]:
    parts: dict[int, NormalizedArtifact] = {}
    for artifact in artifacts:
        metadata = artifact.metadata_json or {}
        part_index = metadata.get("part_index")
        if isinstance(part_index, int) and part_index > 0:
            parts[part_index] = artifact
    return parts


def _artifact_output_counters(
    dataset_file: DatasetFile,
    batch_result: ParserResult,
    write_result: ParquetWriteResult,
    *,
    output_rows: int,
) -> dict[str, Any]:
    return {
        "input_files": 1,
        "input_bytes": dataset_file.file_size_bytes,
        "input_rows": batch_result.rows_read,
        "input_events": batch_result.rows_read,
        "parsed_events": len(batch_result.events),
        "output_rows": output_rows,
        "failed_rows": batch_result.rows_failed,
        "skipped_rows": 0,
        "parser_errors_count": batch_result.parse_errors_count or 0,
        "parquet_size_bytes": write_result.file_size_bytes,
        "write_duration_seconds": write_result.write_duration_seconds,
    }


def _aggregate_output_counters(
    dataset_file: DatasetFile,
    result: ParserResult,
    performance: NormalizationPerformance,
) -> dict[str, Any]:
    return {
        "input_files": 1,
        "input_bytes": dataset_file.file_size_bytes,
        "input_rows": result.rows_read,
        "input_events": result.rows_read,
        "parsed_events": result.events_emitted,
        "output_rows": result.events_emitted,
        "failed_rows": result.rows_failed,
        "skipped_rows": 0,
        "parser_errors_count": result.parse_errors_count or 0,
        "parquet_size_bytes": None,
        "write_duration_seconds": performance.parquet_write_seconds,
    }


def _options_payload(options: NormalizationOptions) -> dict[str, Any]:
    return {
        "workers": options.workers,
        "batch_size": options.batch_size,
        "max_output_part_rows": options.max_output_part_rows,
        "packet_batch_size": options.packet_batch_size,
        "resume": options.resume,
        "packet_mode": options.packet_mode,
        "hash_outputs": options.hash_outputs,
        "sample_size": options.sample_size,
        "resource_profile": options.resource_profile,
        "engine": options.engine,
    }


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__
