from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.categorical_encoding import (
    UNKNOWN_CATEGORY,
    fit_categorical_encoder,
    transform_categorical_features,
)
from scripts.stage_three.preprocessing.fit_transform import (
    fit_preprocessing_artifact,
    transform_with_preprocessing_artifact,
)
from scripts.stage_three.preprocessing.missing_values import PreprocessingFitRoleError
from scripts.stage_three.preprocessing.report import TASK13_REPORT_FILENAME, save_missing_encoding_reports


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"


class CategoricalEncodingTest(unittest.TestCase):
    def test_fit_is_blocked_for_validation_and_test(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)

        with self.assertRaisesRegex(PreprocessingFitRoleError, "TRAIN"):
            fit_categorical_encoder(_train_rows(), role="VALIDATION", feature_catalog=catalog)
        with self.assertRaisesRegex(PreprocessingFitRoleError, "TRAIN"):
            fit_categorical_encoder(_train_rows(), role="TEST", feature_catalog=catalog)

    def test_one_hot_unknown_category_does_not_fail_validation_transform(self) -> None:
        artifact = fit_categorical_encoder(
            _train_rows(),
            role="TRAIN",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        result = transform_categorical_features(
            [{"dns_response_code": "SERVFAIL"}],
            artifact=artifact,
        )

        self.assertEqual(artifact.columns["dns_response_code"].strategy, "one_hot")
        self.assertEqual(result.unknown_counts["dns_response_code"], 1)
        self.assertNotIn("dns_response_code", result.rows[0])
        self.assertEqual(result.rows[0]["dns_response_code__onehot_unknown"], 1)

    def test_high_cardinality_one_hot_falls_back_to_frequency(self) -> None:
        artifact = fit_categorical_encoder(
            [{"network_transport_protocol": f"proto-{index}"} for index in range(20)],
            role="TRAIN",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )
        result = transform_categorical_features(
            [{"network_transport_protocol": "proto-new"}],
            artifact=artifact,
        )

        self.assertEqual(artifact.columns["network_transport_protocol"].strategy, "frequency")
        self.assertEqual(result.rows[0]["network_transport_protocol__freq"], 0.0)
        self.assertEqual(result.unknown_counts["network_transport_protocol"], 1)

    def test_hashing_and_token_id_strategies_are_stable(self) -> None:
        artifact = fit_categorical_encoder(
            [
                {"host_process_name_hash": "powershell.exe", "sequence_event_token": "open"},
                {"host_process_name_hash": "cmd.exe", "sequence_event_token": "write"},
            ],
            role="TRAIN",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )
        first = transform_categorical_features(
            [{"host_process_name_hash": "powershell.exe", "sequence_event_token": "open"}],
            artifact=artifact,
        )
        second = transform_categorical_features(
            [{"host_process_name_hash": "powershell.exe", "sequence_event_token": "open"}],
            artifact=artifact,
        )

        self.assertEqual(artifact.columns["host_process_name_hash"].strategy, "hashing")
        self.assertEqual(first.rows[0]["host_process_name_hash__hash_bucket"], second.rows[0]["host_process_name_hash__hash_bucket"])
        self.assertEqual(artifact.columns["sequence_event_token"].strategy, "token_id")
        self.assertGreater(first.rows[0]["sequence_event_token__token_id"], 0)

    def test_forbidden_source_leakage_fields_are_not_encoded(self) -> None:
        catalog = {
            "feature_groups": {
                "unsafe": {
                    "features": [
                        {
                            "name": "dataset_name",
                            "dtype": "categorical",
                            "allow_in_X": True,
                            "preprocessing": {"encoding": "one_hot"},
                        }
                    ]
                }
            }
        }

        artifact = fit_categorical_encoder(
            [{"dataset_name": "train-a"}],
            role="TRAIN",
            feature_catalog=catalog,
        )

        self.assertNotIn("dataset_name", artifact.columns)
        self.assertIn("dataset_name", artifact.rejected_columns)

    def test_fit_transform_report_includes_task13_required_sections(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        artifact = fit_preprocessing_artifact(
            [
                {"dns_entropy": 2.0, "dns_response_code": "NOERROR"},
                {"dns_entropy": 4.0, "dns_response_code": "NXDOMAIN"},
                {"dns_entropy": None, "dns_response_code": None},
            ],
            role="TRAIN",
            feature_catalog=catalog,
        )
        validation = transform_with_preprocessing_artifact(
            [{"dns_entropy": None, "dns_response_code": "SERVFAIL"}],
            artifact=artifact,
            role="VALIDATION",
        )

        self.assertEqual(validation.artifact.fit_role, "TRAIN")
        self.assertEqual(validation.split_role, "VALIDATION")
        self.assertEqual(validation.rows[0]["dns_entropy"], 3.0)
        self.assertEqual(validation.rows[0]["dns_response_code__onehot_unknown"], 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_missing_encoding_reports(validation)

            en_report = root / "en" / TASK13_REPORT_FILENAME
            self.assertTrue(en_report.exists())
            text = en_report.read_text(encoding="utf-8")
            self.assertIn("Task12-type-casting-and-schema-normalization.md", text)
            self.assertIn("Fit role", text)
            self.assertIn("Imputer Strategies", text)
            self.assertIn("Encoder Strategies", text)
            self.assertIn("Unknown Category Handling", text)
            self.assertIn("Missing Ratios Before/After", text)
            self.assertIn("en", written.report_paths)


def _train_rows() -> list[dict[str, object]]:
    return [
        {"dns_response_code": "NOERROR"},
        {"dns_response_code": "NXDOMAIN"},
        {"dns_response_code": UNKNOWN_CATEGORY},
    ]


if __name__ == "__main__":
    unittest.main()
