from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow.parquet as pq

from scripts.db.models import DatasetFile
from scripts.stage_two.normalization.dns_service import _artifact_output_counters
from scripts.stage_two.parquet.writer import ParquetArtifactWriter, ParquetWriteError
from scripts.stage_two.parsers.base import ParserContext, ParserResult
from scripts.stage_two.parsers.common import build_normalized_event


class ParquetArtifactWriterTest(unittest.TestCase):
    def test_json_fields_are_serialized_before_arrow_type_inference(self) -> None:
        rows = [
            _event(
                "one",
                raw_fields_json={"mixed": 1, "items": [1, "two"]},
                metadata_json={"ttl_mean": 3.5},
            ),
            _event(
                "two",
                raw_fields_json={"mixed": "not-a-number", "items": ["x"]},
                metadata_json={"ttl_mean": " 21:07:56.450015"},
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            result = writer.write_normalized(
                rows,
                branch="dns",
                role="TRAIN",
                modality="dns",
                dataset_slug="mixed-json-smoke",
                schema_version="v1",
                run_id="test",
            )

            table = pq.read_table(result.absolute_path)
            payload = table.to_pylist()
            temp_files = list(result.absolute_path.parent.glob(f".{result.absolute_path.name}.*.tmp"))

        self.assertEqual(result.row_count, 2)
        self.assertGreater(result.file_size_bytes, 0)
        self.assertGreater(result.write_duration_seconds, 0)
        self.assertEqual(result.content_hash_sha256, "")
        self.assertEqual(temp_files, [])
        self.assertIsInstance(payload[0]["raw_fields_json"], str)
        self.assertEqual(json.loads(payload[0]["raw_fields_json"])["mixed"], 1)
        self.assertEqual(json.loads(payload[1]["raw_fields_json"])["mixed"], "not-a-number")
        self.assertEqual(
            json.loads(payload[1]["metadata_json"])["ttl_mean"],
            " 21:07:56.450015",
        )

    def test_lone_surrogates_are_replaced_before_parquet_write(self) -> None:
        rows = [
            _event(
                "bad-surrogate",
                raw_fields_json={"message": "bad\ude88value", "nested": ["ok", "\udc7d"]},
                metadata_json={"details": "meta\udd53value"},
            )
        ]

        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            result = writer.write_normalized(
                rows,
                branch="host",
                role="TEST",
                modality="host",
                dataset_slug="surrogate-smoke",
                schema_version="v1",
                run_id="surrogate",
            )

            payload = pq.read_table(result.absolute_path).to_pylist()

        self.assertEqual(result.row_count, 1)
        self.assertEqual(payload[0]["event_uid"], "bad-surrogate")
        self.assertEqual(json.loads(payload[0]["raw_fields_json"])["message"], "bad?value")
        self.assertEqual(json.loads(payload[0]["raw_fields_json"])["nested"][1], "?")
        self.assertEqual(json.loads(payload[0]["metadata_json"])["details"], "meta?value")

    def test_hash_output_artifacts_hashes_final_file_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory), hash_outputs=True)
            result = writer.write_normalized(
                [_event("one")],
                branch="dns",
                role="TRAIN",
                modality="dns",
                dataset_slug="hash-smoke",
                schema_version="v1",
                run_id="hash",
            )

        self.assertEqual(len(result.content_hash_sha256), 64)

    def test_writer_validates_parquet_metadata_without_materializing_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            with patch(
                "scripts.stage_two.parquet.writer.pq.read_table",
                side_effect=AssertionError("writer validation must not materialize parquet data"),
            ):
                result = writer.write_normalized(
                    [_event("one")],
                    branch="dns",
                    role="TRAIN",
                    modality="dns",
                    dataset_slug="metadata-validation",
                    schema_version="v1",
                    run_id="metadata",
                )

            table = pq.read_table(result.absolute_path)

        self.assertEqual(result.row_count, 1)
        self.assertEqual(table.num_rows, 1)

    def test_empty_artifact_is_rejected_without_explicit_allow_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            with self.assertRaisesRegex(ParquetWriteError, "empty Parquet artifact"):
                writer.write_normalized(
                    [],
                    branch="dns",
                    role="TRAIN",
                    modality="dns",
                    dataset_slug="empty",
                    schema_version="v1",
                    run_id="empty",
                )

            self.assertEqual(list(Path(directory).rglob("*.parquet")), [])

    def test_missing_required_normalized_column_does_not_finalize_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            with self.assertRaisesRegex(ParquetWriteError, "missing required normalized columns"):
                writer.write_normalized(
                    [{"event_uid": "broken"}],
                    branch="dns",
                    role="TRAIN",
                    modality="dns",
                    dataset_slug="broken",
                    schema_version="v1",
                    run_id="broken",
                )

            self.assertEqual(list(Path(directory).rglob("*.parquet")), [])
            self.assertEqual(list(Path(directory).rglob("*.tmp")), [])

    def test_stale_temp_file_is_removed_before_successful_atomic_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            final_path = (
                Path(directory)
                / "parquet"
                / "normalized"
                / "dns"
                / "TRAIN"
                / "dns"
                / "stale-temp"
                / "schema=v1"
                / "part-stale.parquet"
            )
            final_path.parent.mkdir(parents=True, exist_ok=True)
            stale_temp = final_path.with_name(f".{final_path.name}.old.tmp")
            stale_temp.write_text("stale", encoding="utf-8")

            result = writer.write_normalized(
                [_event("one")],
                branch="dns",
                role="TRAIN",
                modality="dns",
                dataset_slug="stale-temp",
                schema_version="v1",
                run_id="stale",
            )

            self.assertTrue(result.absolute_path.exists())
            self.assertFalse(stale_temp.exists())
            self.assertEqual(list(result.absolute_path.parent.glob(f".{result.absolute_path.name}.*.tmp")), [])

    def test_output_counters_match_parser_and_write_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            write_result = writer.write_normalized(
                [_event("one"), _event("two")],
                branch="dns",
                role="TRAIN",
                modality="dns",
                dataset_slug="counters",
                schema_version="v1",
                run_id="counters",
            )

        counters = _artifact_output_counters(
            DatasetFile(
                id=2,
                dataset_id=1,
                file_path="source.csv",
                file_name="source.csv",
                source_format="csv",
                role="TRAIN",
                branch="dns",
                status="READY_FOR_PARSING",
                file_size_bytes=128,
            ),
            ParserResult(
                rows_read=3,
                rows_parsed=2,
                rows_failed=1,
                events=[_event("one"), _event("two")],
            ),
            write_result,
            output_rows=2,
        )

        self.assertEqual(counters["input_files"], 1)
        self.assertEqual(counters["input_bytes"], 128)
        self.assertEqual(counters["input_rows"], 3)
        self.assertEqual(counters["parsed_events"], 2)
        self.assertEqual(counters["output_rows"], 2)
        self.assertEqual(counters["failed_rows"], 1)
        self.assertEqual(counters["parser_errors_count"], 1)
        self.assertEqual(counters["parquet_size_bytes"], write_result.file_size_bytes)


def _event(
    event_uid: str,
    *,
    raw_fields_json: dict[str, object] | None = None,
    metadata_json: dict[str, object] | None = None,
) -> dict[str, object]:
    return build_normalized_event(
        _context(),
        parser_name="dns_csv_parser",
        parser_version="v1",
        schema_name="normalized_event",
        schema_version="v1",
        event_uid=event_uid,
        event_index=0,
        entity_type="domain",
        entity_id="example.org",
        event_type="dns_query",
        modality="dns",
        query_domain="example.org",
        raw_fields_json=raw_fields_json or {"query_domain": "example.org"},
        metadata_json=metadata_json,
    )


def _context() -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="dataset",
        dataset_role="TRAIN",
        branch="dns",
        source_format="csv",
        source_file_path="source.csv",
        source_file_hash="hash",
        parser_run_id=3,
    )


if __name__ == "__main__":
    unittest.main()
