from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.report import TASK12_REPORT_FILENAME, save_type_casting_reports
from scripts.stage_three.preprocessing.type_casting import cast_x_batches_to_typed_table, cast_x_rows_to_typed_table


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"


class TypeCastingTest(unittest.TestCase):
    def test_casts_catalog_features_to_ml_compatible_arrow_dtypes(self) -> None:
        result = cast_x_rows_to_typed_table(
            _sample_x_rows(),
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        self.assertEqual(result.status, "PARTIAL_SUCCESS")
        schema = result.typed_X.schema
        self.assertEqual(schema.field("dns_query_length").type, pa.int32())
        self.assertEqual(schema.field("dns_entropy").type, pa.float32())
        self.assertEqual(schema.field("network_flow_duration_ms").type, pa.float32())
        self.assertEqual(schema.field("host_auth_failure_flag").type, pa.int8())
        self.assertEqual(schema.field("host_syscall_frequency_vector").type, pa.list_(pa.float32()))
        self.assertEqual(schema.field("sequence_length").type, pa.int64())

        rejected = {item.column: item.reason for item in result.rejected_columns}
        self.assertIn("dns_response_code", rejected)
        self.assertIn("scheduled for categorical/token encoding", rejected["dns_response_code"])
        self.assertIn("event_timestamp", rejected)
        self.assertIn("raw_payload_body", rejected)
        self.assertIn("source_path", rejected)
        self.assertNotIn("dns_response_code", result.typed_columns)
        self.assertNotIn("event_timestamp", result.typed_columns)
        self.assertGreater(result.memory_before_bytes, result.memory_after_bytes)

    def test_rejects_non_integer_values_for_integer_catalog_features(self) -> None:
        result = cast_x_rows_to_typed_table(
            [{"dns_query_length": 10.5, "dns_entropy": 3.0}],
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        rejected = {item.column: item.reason for item in result.rejected_columns}
        self.assertIn("dns_query_length", rejected)
        self.assertIn("non-integer", rejected["dns_query_length"])
        self.assertIn("dns_entropy", result.typed_columns)

    def test_rejects_dict_json_like_values_from_typed_x(self) -> None:
        result = cast_x_rows_to_typed_table(
            [{"dns_entropy": {"raw": 1.0}, "dns_query_length": 11}],
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        rejected = {item.column: item.reason for item in result.rejected_columns}
        self.assertIn("dns_entropy", rejected)
        self.assertNotIn("dns_entropy", result.typed_columns)
        self.assertIn("dns_query_length", result.typed_columns)

    def test_report_includes_task12_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = cast_x_rows_to_typed_table(
                _sample_x_rows(),
                feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
            )
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_type_casting_reports(result)

            ru_report = root / "ru" / TASK12_REPORT_FILENAME
            en_report = root / "en" / TASK12_REPORT_FILENAME
            self.assertTrue(ru_report.exists())
            self.assertTrue(en_report.exists())
            text = en_report.read_text(encoding="utf-8")
            self.assertIn("Task11-xy-metadata-traceability-separation.md", text)
            self.assertIn("Dtype Conversions", text)
            self.assertIn("Rejected Columns", text)
            self.assertIn("Memory before", text)
            self.assertIn("Schema Warnings", text)
            self.assertIn("ru", written.report_paths)
            self.assertIn("en", written.report_paths)

    def test_batch_api_preserves_schema_normalization(self) -> None:
        rows = _sample_x_rows()
        result = cast_x_batches_to_typed_table(
            [rows[:1], rows[1:]],
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        self.assertEqual(result.row_count, 2)
        self.assertEqual(result.typed_X.schema.field("dns_entropy").type, pa.float32())


def _sample_x_rows() -> list[dict[str, object]]:
    return [
        {
            "dns_query_length": "11",
            "dns_entropy": "3.25",
            "network_flow_duration_ms": 123.5,
            "host_auth_failure_flag": True,
            "host_syscall_frequency_vector": [1, 2, 3],
            "sequence_length": 2**40,
            "dns_response_code": "NOERROR",
            "event_timestamp": "2026-07-06T00:00:00Z",
            "raw_payload_body": "secret-body",
            "source_path": r"C:\datasets\proposal\raw\dns.csv",
        },
        {
            "dns_query_length": 12,
            "dns_entropy": 2.75,
            "network_flow_duration_ms": None,
            "host_auth_failure_flag": "false",
            "host_syscall_frequency_vector": [0, 1, 0],
            "sequence_length": 2**40 + 1,
            "dns_response_code": "NXDOMAIN",
            "event_timestamp": None,
            "raw_payload_body": "secret-body",
            "source_path": r"C:\datasets\proposal\raw\dns.csv",
        },
    ]


if __name__ == "__main__":
    unittest.main()
