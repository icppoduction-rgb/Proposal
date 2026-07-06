from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.model_ready import (
    ForbiddenXColumnError,
    separate_feature_artifact_rows,
    separate_feature_artifacts,
    validate_no_forbidden_x_columns,
)
from scripts.stage_three.model_ready.report import TASK11_REPORT_FILENAME, save_xy_separation_reports


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"


class XYSeparationTest(unittest.TestCase):
    def test_separates_x_y_metadata_and_traceability_on_sample_rows(self) -> None:
        result = separate_feature_artifact_rows(
            _sample_feature_rows(),
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.row_count, 2)
        self.assertEqual(
            result.x_columns,
            ["dns_query_length", "dns_entropy", "host_auth_failure_flag", "network_flow_bytes"],
        )
        self.assertEqual(set(result.y_columns), {"sample_uid", "label_binary", "label_status", "label_source"})
        self.assertIn("dataset_name", result.metadata_columns)
        self.assertIn("parser_version", result.metadata_columns)
        self.assertIn("event_uid", result.traceability_columns)
        self.assertIn("source_path", result.traceability_columns)

        for x_row in result.tables.X:
            self.assertNotIn("label_binary", x_row)
            self.assertNotIn("dataset_name", x_row)
            self.assertNotIn("source_path", x_row)
            self.assertNotIn("event_uid", x_row)
            self.assertEqual(set(x_row), set(result.x_columns))

        dropped = {item.name: item.reason for item in result.dropped_columns}
        self.assertEqual(dropped["label_binary"], "target label stored in y")
        self.assertEqual(dropped["source_path"], "forbidden in X; stored in traceability")
        self.assertEqual(dropped["unknown_debug_field"], "not declared allow_in_X in feature_catalog")

    def test_reads_feature_artifacts_from_parquet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "features.parquet"
            pq.write_table(pa.Table.from_pylist(_sample_feature_rows()), artifact_path)

            result = separate_feature_artifacts(
                [artifact_path],
                feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
            )

        self.assertEqual(result.row_count, 2)
        self.assertEqual(len(result.tables.X), 2)
        self.assertEqual(len(result.tables.y), 2)
        self.assertEqual(len(result.tables.metadata), 2)
        self.assertEqual(len(result.tables.traceability), 2)

    def test_forbidden_x_columns_check_fails_on_non_null_forbidden_column(self) -> None:
        with self.assertRaisesRegex(ForbiddenXColumnError, "label_binary=1"):
            validate_no_forbidden_x_columns([{"dns_query_length": 10, "label_binary": 1}])

    def test_absolute_local_path_check_fails_inside_x_value(self) -> None:
        with self.assertRaisesRegex(ForbiddenXColumnError, "absolute_path=1"):
            validate_no_forbidden_x_columns([{"dns_query_length": 10, "encoded_path": r"C:\tmp\payload.bin"}])

    def test_report_includes_required_task11_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = separate_feature_artifact_rows(
                _sample_feature_rows(),
                feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
            )
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_xy_separation_reports(result)

            ru_report = root / "ru" / TASK11_REPORT_FILENAME
            en_report = root / "en" / TASK11_REPORT_FILENAME
            self.assertTrue(ru_report.exists())
            self.assertTrue(en_report.exists())
            text = en_report.read_text(encoding="utf-8")
            self.assertIn("Task10-label-alignment-policies.md", text)
            self.assertIn("X Columns Kept", text)
            self.assertIn("y Columns", text)
            self.assertIn("Metadata Columns", text)
            self.assertIn("Traceability Columns", text)
            self.assertIn("Dropped/Forbidden Columns", text)
            self.assertIn("ru", written.report_paths)
            self.assertIn("en", written.report_paths)


def _sample_feature_rows() -> list[dict[str, object]]:
    return [
        {
            "sample_uid": "s1",
            "event_uid": "e1",
            "dataset_name": "proposal-dns",
            "dataset_role": "TRAIN",
            "branch": "dns",
            "feature_group": "dns_lexical",
            "source_path": r"C:\datasets\proposal\raw\dns-1.csv",
            "parser_name": "dns_parser",
            "parser_version": "1.0",
            "raw_fields_json": '{"domain":"example.com"}',
            "metadata_json": '{"audit":true}',
            "dns_query_length": 11,
            "dns_entropy": 3.2,
            "host_auth_failure_flag": False,
            "network_flow_bytes": 100.0,
            "label_binary": 1,
            "label_status": "explicit_label",
            "label_source": "fixture",
            "unknown_debug_field": "debug-only",
        },
        {
            "sample_uid": "s2",
            "event_uid": "e2",
            "dataset_name": "proposal-dns",
            "dataset_role": "TRAIN",
            "branch": "dns",
            "feature_group": "dns_lexical",
            "source_path": r"C:\datasets\proposal\raw\dns-2.csv",
            "parser_name": "dns_parser",
            "parser_version": "1.0",
            "raw_fields_json": '{"domain":"openai.com"}',
            "metadata_json": '{"audit":true}',
            "dns_query_length": 10,
            "dns_entropy": 2.8,
            "host_auth_failure_flag": True,
            "network_flow_bytes": 200.0,
            "label_binary": 0,
            "label_status": "explicit_label",
            "label_source": "fixture",
            "unknown_debug_field": "debug-only",
        },
    ]


if __name__ == "__main__":
    unittest.main()
