from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.db.models import Dataset, DatasetFile
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.normalization.options import NormalizationOptions
from scripts.stage_two.normalization.performance import NormalizationPerformance
from scripts.stage_two.parquet.writer import ParquetWriteResult
from scripts.stage_two.parsers.base import ParserContext, ParserResult


class NormalizationBatchStatusTest(unittest.TestCase):
    def test_host_service_preserves_skipped_status_from_no_event_batch(self) -> None:
        service = HostNormalizationService.__new__(HostNormalizationService)
        service.options = NormalizationOptions(batch_size=100, max_output_part_rows=100)
        dataset_file = DatasetFile(
            id=1,
            dataset_id=2,
            file_path="helper.txt",
            file_name="helper.txt",
            source_format="txt",
            role="TRAIN",
            branch="host",
            status="READY_FOR_PARSING",
            file_size_bytes=10,
        )
        context = ParserContext(
            dataset_id=2,
            file_id=1,
            dataset_name="host-train-txt",
            dataset_role="TRAIN",
            branch="host",
            source_format="txt",
            source_file_path="helper.txt",
            source_file_hash="hash",
            parser_run_id=3,
        )

        def parse_batches(*_: object, **__: object):
            yield ParserResult(
                rows_read=0,
                rows_parsed=0,
                rows_failed=0,
                events=[],
                warnings=["parser_report_status=SKIPPED"],
                status_override="SKIPPED",
                status_reason="helper file",
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "helper.txt"
            path.write_text("helper", encoding="utf-8")
            result, artifact, output_path, _modality = service._parse_and_write_batches(
                parse_batches,
                path,
                context,
                dataset_file=dataset_file,
                parser_run_id=3,
                schema_version_id=4,
                schema_name="normalized_event",
                schema_version="v1",
                performance=NormalizationPerformance(),
            )

        self.assertIsNone(artifact)
        self.assertIsNone(output_path)
        self.assertEqual(result.file_status, "SKIPPED")
        self.assertEqual(result.parser_run_status, "SKIPPED")
        self.assertEqual(result.status_decision.reason, "helper file")

    def test_host_service_commits_each_written_part_outside_nested_transaction(self) -> None:
        service = HostNormalizationService.__new__(HostNormalizationService)
        session = _FakeSession(nested=False)
        writer = _FakeWriter()
        service.session = session
        service.options = NormalizationOptions(batch_size=100, max_output_part_rows=2)
        service.writer = writer
        service.artifact_repository = object()
        dataset_file = _dataset_file()
        context = _parser_context()

        def parse_batches(*_: object, **__: object):
            yield ParserResult(
                rows_read=3,
                rows_parsed=3,
                rows_failed=0,
                events=[_event(1), _event(2), _event(3)],
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.txt"
            path.write_text("events", encoding="utf-8")
            result, artifact, output_path, _modality = service._parse_and_write_batches(
                parse_batches,
                path,
                context,
                dataset_file=dataset_file,
                parser_run_id=3,
                schema_version_id=4,
                schema_name="normalized_event",
                schema_version="v1",
                performance=NormalizationPerformance(),
            )

        self.assertIsNotNone(artifact)
        self.assertEqual(output_path, "normalized/part-3-*.parquet")
        self.assertEqual(result.events_emitted, 3)
        self.assertEqual(writer.write_row_counts, [2, 1])
        self.assertEqual(session.commit_count, 2)
        self.assertEqual(session.flush_count, 0)

    def test_host_service_flushes_each_written_part_inside_nested_transaction(self) -> None:
        service = HostNormalizationService.__new__(HostNormalizationService)
        session = _FakeSession(nested=True)
        service.session = session
        service.options = NormalizationOptions(batch_size=100, max_output_part_rows=2)
        service.writer = _FakeWriter()
        service.artifact_repository = object()
        dataset_file = _dataset_file()
        context = _parser_context()

        def parse_batches(*_: object, **__: object):
            yield ParserResult(
                rows_read=2,
                rows_parsed=2,
                rows_failed=0,
                events=[_event(1), _event(2)],
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.txt"
            path.write_text("events", encoding="utf-8")
            service._parse_and_write_batches(
                parse_batches,
                path,
                context,
                dataset_file=dataset_file,
                parser_run_id=3,
                schema_version_id=4,
                schema_name="normalized_event",
                schema_version="v1",
                performance=NormalizationPerformance(),
            )

        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.flush_count, 1)


class _FakeSession:
    def __init__(self, *, nested: bool) -> None:
        self._nested = nested
        self.commit_count = 0
        self.flush_count = 0

    def in_nested_transaction(self) -> bool:
        return self._nested

    def commit(self) -> None:
        self.commit_count += 1

    def flush(self) -> None:
        self.flush_count += 1


class _FakeWriter:
    def __init__(self) -> None:
        self.write_row_counts: list[int] = []

    def write_normalized(
        self,
        rows: list[dict[str, Any]],
        **metadata: Any,
    ) -> ParquetWriteResult:
        self.write_row_counts.append(len(rows))
        run_id = metadata["run_id"]
        return ParquetWriteResult(
            absolute_path=Path(f"C:/tmp/part-{run_id}.parquet"),
            relative_path=f"normalized/part-{run_id}.parquet",
            row_count=len(rows),
            file_size_bytes=128,
            content_hash_sha256="",
            write_duration_seconds=0.01,
        )

    def register_normalized_artifact(
        self,
        repository: object,
        result: ParquetWriteResult,
        **metadata: Any,
    ) -> "_FakeArtifact":
        return _FakeArtifact(result.relative_path, metadata)


class _FakeArtifact:
    def __init__(self, normalized_path: str, metadata_json: dict[str, Any]) -> None:
        self.normalized_path = normalized_path
        self.metadata_json = metadata_json


def _dataset_file() -> DatasetFile:
    return DatasetFile(
        id=1,
        dataset_id=2,
        dataset=Dataset(
            id=2,
            name="host-validation-netflow-day",
            slug="host-validation-netflow-day",
            role="VALIDATION",
            branch="host",
        ),
        file_path="events.txt",
        file_name="events.txt",
        source_format="netflow_day",
        role="VALIDATION",
        branch="host",
        status="READY_FOR_PARSING",
        file_size_bytes=10,
    )


def _parser_context() -> ParserContext:
    return ParserContext(
        dataset_id=2,
        file_id=1,
        dataset_name="host-validation-netflow-day",
        dataset_role="VALIDATION",
        branch="host",
        source_format="netflow_day",
        source_file_path="events.txt",
        source_file_hash="hash",
        parser_run_id=3,
    )


def _event(index: int) -> dict[str, Any]:
    return {
        "event_uid": f"event-{index}",
        "modality": "network_flow",
    }


if __name__ == "__main__":
    unittest.main()
