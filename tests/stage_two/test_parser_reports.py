from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from scripts.db.models import DatasetFile, ParserRegistry, ParserRun
from scripts.stage_two.parsers import ParserResult
from scripts.stage_two.reports import save_parser_run_reports


class ParserRunReportTest(unittest.TestCase):
    def test_save_parser_run_reports_writes_four_json_reports(self) -> None:
        result = ParserResult(
            rows_read=2,
            rows_parsed=1,
            rows_failed=1,
            events=[{"event_uid": "sample"}],
            warnings=["base64_detected=True", "compression_hint=gzip"],
            error_samples=["missing required fields: " + ("x" * 1600)],
        )
        parser_run = _parser_run(status="PARTIAL_SUCCESS")
        dataset_file = _dataset_file()
        registry = _parser_registry()

        with TemporaryDirectory() as tmp:
            paths = save_parser_run_reports(
                parser_run=parser_run,
                dataset_file=dataset_file,
                parser_result=result,
                parser_registry=registry,
                output_artifact_path="parquet/normalized/dns/TRAIN/dns/sample.parquet",
                storage_root=tmp,
            )

            self.assertEqual(
                set(paths),
                {
                    "en_parser_json",
                    "ru_parser_json",
                    "en_normalization_json",
                    "ru_normalization_json",
                },
            )
            for relative_path in paths.values():
                self.assertTrue((Path(tmp) / relative_path).exists())

            payload = json.loads((Path(tmp) / paths["en_parser_json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["parser_name"], "dns_csv_parser")
            self.assertEqual(payload["parser_version"], "v1")
            self.assertEqual(payload["branch"], "dns")
            self.assertEqual(payload["role"], "TRAIN")
            self.assertEqual(payload["source_format"], "csv")
            self.assertEqual(payload["dataset_id"], 10)
            self.assertEqual(payload["file_id"], 20)
            self.assertEqual(payload["source_file_hash"], "abc123")
            self.assertEqual(payload["rows_read"], 2)
            self.assertEqual(payload["rows_parsed"], 1)
            self.assertEqual(payload["rows_failed"], 1)
            self.assertEqual(payload["status"], "PARTIAL_SUCCESS")
            self.assertTrue(payload["read_hints"]["base64_detected"])
            self.assertEqual(payload["read_hints"]["compression_hint"], "gzip")
            self.assertIn("[truncated]", payload["errors_sample"][0])
            self.assertEqual(payload["schema_mismatch_counters"]["schema_mismatch"], 1)

    def test_save_parser_run_reports_handles_failed_run_without_parser_result(self) -> None:
        parser_run = _parser_run(status="FAILED", error_message="parser class unavailable")
        dataset_file = _dataset_file(status="FAILED")

        with TemporaryDirectory() as tmp:
            paths = save_parser_run_reports(
                parser_run=parser_run,
                dataset_file=dataset_file,
                error_message="parser class unavailable",
                storage_root=tmp,
            )

            payload = json.loads((Path(tmp) / paths["en_parser_json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "FAILED")
            self.assertEqual(payload["file_status"], "FAILED")
            self.assertEqual(payload["error_message"], "parser class unavailable")
            self.assertIsNone(payload["rows_read"])


def _parser_run(*, status: str, error_message: str | None = None) -> ParserRun:
    return ParserRun(
        id=30,
        run_uid=uuid4(),
        file_id=20,
        parser_registry_id=40,
        schema_version_id=4,
        parser_name="dns_csv_parser",
        parser_version="v1",
        status=status,
        output_parquet_path="parquet/normalized/dns/TRAIN/dns/sample.parquet",
        error_message=error_message,
        started_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
    )


def _dataset_file(*, status: str = "PARTIALLY_PARSED") -> DatasetFile:
    return DatasetFile(
        id=20,
        dataset_id=10,
        file_path="C:/datasets/dns/train/sample.csv",
        relative_path="dns/train/sample.csv",
        file_name="sample.csv",
        source_format="csv",
        file_hash_sha256="abc123",
        role="TRAIN",
        branch="dns",
        status=status,
        encoding_hint="utf-8",
    )


def _parser_registry() -> ParserRegistry:
    return ParserRegistry(
        id=40,
        parser_name="dns_csv_parser",
        parser_version="v1",
        branch="dns",
        source_format="csv",
        normalized_schema_name="normalized_event",
        normalized_schema_version="v1",
        parser_module="scripts.stage_two.parsers.dns",
        parser_class="DnsCsvParser",
        priority=10,
        is_active=True,
        supports_streaming=True,
        requires_external_tools=False,
    )


if __name__ == "__main__":
    unittest.main()
