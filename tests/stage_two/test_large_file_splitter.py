from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.db.models import DatasetFile
from scripts.stage_two.cli import _parse_split_large_files_args
from scripts.stage_two.splitting.large_files import SplitLargeFilesRequest, SplitLargeFilesService, _split_line_file
from scripts.stage_two.traceability.service import dataset_file_metadata


class LargeFileSplitterTest(unittest.TestCase):
    def test_split_line_file_preserves_lines_and_repeats_header(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = directory / "dataset.csv"
        source.write_text("a,b\n1,2\n3,4\n5,6\n7,8\n", encoding="utf-8")

        chunks = _split_line_file(
            source,
            output_dir=directory / "parts",
            max_part_size_bytes=8,
            has_header=True,
            overwrite=False,
        )

        self.assertGreater(len(chunks), 1)
        payloads = [chunk.path.read_text(encoding="utf-8") for chunk in chunks]
        self.assertEqual(payloads[0], "a,b\n1,2\n")
        self.assertTrue(all(payload.startswith("a,b\n") for payload in payloads))
        data_lines = [
            line
            for payload in payloads
            for line in payload.splitlines()
            if line != "a,b"
        ]
        self.assertEqual(data_lines, ["1,2", "3,4", "5,6", "7,8"])
        self.assertEqual(chunks[0].line_start, 2)
        self.assertEqual(chunks[0].line_end, 2)
        self.assertIsNotNone(chunks[0].byte_start)
        self.assertIsNotNone(chunks[0].byte_end)
        self.assertEqual(len(chunks[0].chunk_hash_sha256), 64)

    def test_parse_split_large_files_args(self) -> None:
        request = _parse_split_large_files_args(
            [
                "--branch",
                "DNS",
                "--role",
                "test",
                "--format",
                "csv",
                "--limit",
                "2",
                "--max-part-size-mb",
                "512",
                "--min-size-mb",
                "64",
                "--header",
                "no",
                "--apply",
                "--register",
            ]
        )

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.role, "TEST")
        self.assertEqual(request.source_format, "csv")
        self.assertEqual(request.limit, 2)
        self.assertEqual(request.max_part_size_bytes, 512 * 1024 * 1024)
        self.assertEqual(request.min_file_size_bytes, 64 * 1024 * 1024)
        self.assertEqual(request.header_mode, "no")
        self.assertTrue(request.apply_changes)
        self.assertTrue(request.register)

    def test_service_dry_run_does_not_create_parts_or_register(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = _write_source(directory, "large.csv", "a,b\n1,2\n3,4\n5,6\n")
        file = _dataset_file(source, source_format="csv")
        repository = _FakeDatasetFileRepository()
        service = _service_with_files([file], repository)

        result = service.split_large_files(
            _request(source_format="csv", apply_changes=False, register=False, max_part_size_bytes=8)
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.files[0].status, "DRY_RUN")
        self.assertGreater(result.chunks_created, 1)
        self.assertFalse((directory / "large.csv.parts").exists())
        self.assertEqual(repository.upsert_rows, [])

    def test_service_apply_creates_chunks_without_catalog_registration(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = _write_source(directory, "large.csv", "a,b\n1,2\n3,4\n5,6\n")
        file = _dataset_file(source, source_format="csv")
        repository = _FakeDatasetFileRepository()
        service = _service_with_files([file], repository)

        result = service.split_large_files(
            _request(source_format="csv", apply_changes=True, register=False, max_part_size_bytes=8)
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.files[0].status, "SPLIT")
        self.assertGreater(result.chunks_created, 1)
        self.assertEqual(result.registered, 0)
        self.assertEqual(file.status, "READY_FOR_PARSING")
        self.assertTrue(Path(result.files[0].output_dir or "").exists())

    def test_service_registers_chunks_and_skips_parent_after_successful_registration(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = _write_source(directory, "large.csv", "a,b\n1,2\n3,4\n5,6\n")
        file = _dataset_file(source, source_format="csv")
        repository = _FakeDatasetFileRepository()
        service = _service_with_files([file], repository)

        result = service.split_large_files(
            _request(source_format="csv", apply_changes=True, register=True, max_part_size_bytes=8)
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.registered, result.chunks_created)
        self.assertTrue(repository.force_status)
        self.assertEqual(file.status, "SKIPPED")
        row = repository.upsert_rows[0]
        metadata = row["metadata_json"]
        self.assertEqual(row["status"], "READY_FOR_PARSING")
        self.assertEqual(row["file_hash_sha256"], metadata["chunk_hash_sha256"])
        self.assertEqual(metadata["parent_file_id"], file.id)
        self.assertEqual(metadata["chunk_index"], 1)
        self.assertEqual(metadata["chunk_path"], row["file_path"])
        self.assertEqual(metadata["original_source_path"], str(source))
        self.assertTrue(metadata["source_order_preserved"])
        self.assertEqual(metadata["line_start"], 2)
        self.assertIsNotNone(metadata["byte_start"])

    def test_keep_source_ready_preserves_parent_status_after_register(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = _write_source(directory, "large.csv", "a,b\n1,2\n3,4\n5,6\n")
        file = _dataset_file(source, source_format="csv")
        repository = _FakeDatasetFileRepository()
        service = _service_with_files([file], repository)

        result = service.split_large_files(
            _request(
                source_format="csv",
                apply_changes=True,
                register=True,
                keep_source_ready=True,
                max_part_size_bytes=8,
            )
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.registered, result.chunks_created)
        self.assertEqual(file.status, "READY_FOR_PARSING")
        self.assertEqual(repository.marked_statuses, [])

    def test_binary_formats_are_not_split_by_line_splitter(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = _write_source(directory, "capture.pcap", "not really a packet capture")
        file = _dataset_file(source, source_format="pcap")
        repository = _FakeDatasetFileRepository()
        service = _service_with_files([file], repository)

        result = service.split_large_files(
            _request(source_format="pcap", apply_changes=True, register=True, max_part_size_bytes=8)
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.files[0].status, "SKIPPED_UNSUPPORTED_FORMAT")
        self.assertEqual(result.chunks_created, 0)
        self.assertEqual(repository.upsert_rows, [])

    def test_traceability_metadata_exposes_chunk_parent_link(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        chunk_path = _write_source(directory, "large.part-000001.csv", "a,b\n1,2\n")
        file = _dataset_file(chunk_path, source_format="csv")
        file.metadata_json = {
            "parent_file_id": 10,
            "chunk_index": 1,
            "chunk_path": str(chunk_path),
            "byte_start": 4,
            "byte_end": 8,
            "line_start": 2,
            "line_end": 2,
            "source_order_preserved": True,
            "original_source_path": str(directory / "large.csv"),
        }

        payload = dataset_file_metadata(file)

        self.assertTrue(payload["chunk"]["is_chunk"])
        self.assertEqual(payload["chunk"]["parent_file_id"], 10)
        self.assertEqual(payload["chunk"]["chunk_index"], 1)
        self.assertEqual(payload["chunk"]["line_start"], 2)
        self.assertTrue(payload["chunk"]["source_order_preserved"])


def _write_source(directory: Path, name: str, content: str) -> Path:
    source = directory / name
    source.write_text(content, encoding="utf-8")
    return source


def _dataset_file(path: Path, *, source_format: str) -> DatasetFile:
    return DatasetFile(
        id=10,
        dataset_id=20,
        file_path=str(path),
        relative_path=path.name,
        file_name=path.name,
        file_extension=path.suffix,
        source_format=source_format,
        file_size_bytes=path.stat().st_size,
        file_hash_sha256="parent-hash",
        role="TRAIN",
        branch="host",
        status="READY_FOR_PARSING",
    )


def _request(
    *,
    source_format: str,
    apply_changes: bool,
    register: bool,
    max_part_size_bytes: int,
    keep_source_ready: bool = False,
) -> SplitLargeFilesRequest:
    return SplitLargeFilesRequest(
        branch="host",
        role="TRAIN",
        source_format=source_format,
        max_part_size_bytes=max_part_size_bytes,
        min_file_size_bytes=0,
        apply_changes=apply_changes,
        register=register,
        keep_source_ready=keep_source_ready,
        header_mode="auto",
    )


def _service_with_files(
    files: list[DatasetFile],
    repository: "_FakeDatasetFileRepository",
) -> SplitLargeFilesService:
    service = SplitLargeFilesService.__new__(SplitLargeFilesService)
    service.session = None  # type: ignore[assignment]
    service.file_repository = repository  # type: ignore[assignment]
    service._selected_files = lambda request: files  # type: ignore[method-assign]
    return service


class _FakeDatasetFileRepository:
    def __init__(self) -> None:
        self.upsert_rows: list[dict[str, Any]] = []
        self.force_status = False
        self.marked_statuses: list[str] = []

    def bulk_upsert_files(self, rows: list[dict[str, Any]], *, force_status: bool = False) -> int:
        self.upsert_rows.extend(rows)
        self.force_status = force_status
        return len(rows)

    def mark_file_status(
        self,
        file: DatasetFile,
        status: str,
        *,
        error_message: str | None = None,
    ) -> DatasetFile:
        file.status = status
        file.error_message = error_message
        self.marked_statuses.append(status)
        return file


if __name__ == "__main__":
    unittest.main()
