from __future__ import annotations

import unittest
from pathlib import Path

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.missing_values import (
    PreprocessingFitRoleError,
    fit_missing_value_imputer,
    transform_missing_values,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"


class MissingValuesTest(unittest.TestCase):
    def test_fit_is_blocked_for_validation_and_test(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)

        with self.assertRaisesRegex(PreprocessingFitRoleError, "TRAIN"):
            fit_missing_value_imputer(_train_rows(), role="VALIDATION", feature_catalog=catalog)
        with self.assertRaisesRegex(PreprocessingFitRoleError, "TRAIN"):
            fit_missing_value_imputer(_train_rows(), role="TEST", feature_catalog=catalog)

    def test_train_fit_artifact_stores_strategies_and_statistics(self) -> None:
        artifact = fit_missing_value_imputer(
            _train_rows(),
            role="TRAIN",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        self.assertEqual(artifact.fit_role, "TRAIN")
        self.assertEqual(artifact.columns["dns_query_length"].strategy, "zero")
        self.assertEqual(artifact.columns["dns_query_length"].fill_value, 0)
        self.assertEqual(artifact.columns["dns_entropy"].strategy, "median")
        self.assertEqual(artifact.columns["dns_entropy"].fill_value, 3.0)
        self.assertEqual(artifact.columns["host_auth_failure_flag"].strategy, "false")
        self.assertEqual(artifact.columns["host_auth_failure_flag"].fill_value, 0)
        self.assertEqual(artifact.columns["dns_response_code"].strategy, "unknown")
        self.assertEqual(artifact.columns["dns_response_code"].fill_value, "UNKNOWN")

    def test_validation_transform_uses_train_artifact_and_adds_indicators(self) -> None:
        artifact = fit_missing_value_imputer(
            _train_rows(),
            role="TRAIN",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        result = transform_missing_values(_validation_rows(), artifact=artifact)

        self.assertEqual(result.rows[0]["dns_query_length"], 0)
        self.assertEqual(result.rows[0]["dns_entropy"], 3.0)
        self.assertEqual(result.rows[0]["host_auth_failure_flag"], 0)
        self.assertEqual(result.rows[0]["dns_response_code"], "UNKNOWN")
        self.assertEqual(result.rows[0]["dns_entropy__missing"], 1)
        self.assertEqual(result.rows[0]["host_auth_failure_flag__missing"], 1)
        self.assertEqual(result.missing_ratios_before["dns_entropy"], 1.0)
        self.assertEqual(result.missing_ratios_after["dns_entropy"], 0.0)


def _train_rows() -> list[dict[str, object]]:
    return [
        {
            "dns_query_length": 10,
            "dns_entropy": 2.0,
            "host_auth_failure_flag": True,
            "dns_response_code": "NOERROR",
        },
        {
            "dns_query_length": None,
            "dns_entropy": 4.0,
            "host_auth_failure_flag": None,
            "dns_response_code": None,
        },
    ]


def _validation_rows() -> list[dict[str, object]]:
    return [
        {
            "dns_query_length": None,
            "dns_entropy": None,
            "host_auth_failure_flag": None,
            "dns_response_code": "",
        }
    ]


if __name__ == "__main__":
    unittest.main()
