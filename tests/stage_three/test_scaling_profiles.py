from __future__ import annotations

import math
import unittest
from pathlib import Path

import pyarrow as pa

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.missing_values import PreprocessingFitRoleError
from scripts.stage_three.preprocessing.profiles import (
    DL_SCALED_PROFILE,
    TREE_UNSCALED_PROFILE,
)
from scripts.stage_three.preprocessing.scaling import (
    available_scaling_profiles,
    fit_scaling_artifact,
    transform_scaling,
    transform_scaling_table,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"


class ScalingProfilesTest(unittest.TestCase):
    def test_tree_unscaled_and_dl_scaled_profiles_are_available(self) -> None:
        profiles = available_scaling_profiles()

        self.assertIn(TREE_UNSCALED_PROFILE, profiles)
        self.assertIn(DL_SCALED_PROFILE, profiles)
        self.assertEqual(profiles[TREE_UNSCALED_PROFILE]["default_scaler"], "none")
        self.assertEqual(set(profiles[DL_SCALED_PROFILE]["allowed_scalers"]), {"minmax", "standard"})

    def test_fit_is_blocked_for_validation_and_test(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)

        with self.assertRaisesRegex(PreprocessingFitRoleError, "TRAIN"):
            fit_scaling_artifact(_train_rows(), role="VALIDATION", profile_name="standard_scaled", feature_catalog=catalog)
        with self.assertRaisesRegex(PreprocessingFitRoleError, "TRAIN"):
            fit_scaling_artifact(_train_rows(), role="TEST", profile_name="standard_scaled", feature_catalog=catalog)

    def test_standard_scaler_fits_train_and_transforms_other_splits(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        artifact = fit_scaling_artifact(
            _train_rows(),
            role="TRAIN",
            profile_name="standard_scaled",
            feature_catalog=catalog,
        )

        validation = transform_scaling([{"dns_entropy": 4.0}], artifact=artifact, role="VALIDATION")
        test = transform_scaling([{"dns_entropy": 6.0}], artifact=artifact, role="TEST")

        self.assertEqual(artifact.fit_role, "TRAIN")
        self.assertEqual(artifact.columns["dns_entropy"].strategy, "standard")
        self.assertAlmostEqual(artifact.columns["dns_entropy"].mean or 0.0, 4.0)
        self.assertAlmostEqual(validation.rows[0]["dns_entropy"], 0.0)
        self.assertAlmostEqual(test.rows[0]["dns_entropy"], math.sqrt(1.5), places=6)

    def test_tree_unscaled_leaves_rows_unchanged(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        artifact = fit_scaling_artifact(
            _train_rows(),
            role="TRAIN",
            profile_name=TREE_UNSCALED_PROFILE,
            feature_catalog=catalog,
        )
        result = transform_scaling([{"dns_entropy": 5.0}], artifact=artifact, role="TEST")

        self.assertEqual(artifact.feature_count, 0)
        self.assertEqual(artifact.columns, {})
        self.assertEqual(result.rows[0]["dns_entropy"], 5.0)

    def test_dl_scaled_uses_only_standard_or_minmax_by_feature_policy(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        artifact = fit_scaling_artifact(
            [
                {"dns_entropy": 2.0, "dns_suspicious_tunnel_score": 0.1, "dns_queries_per_window": 10},
                {"dns_entropy": 6.0, "dns_suspicious_tunnel_score": 0.9, "dns_queries_per_window": 30},
            ],
            role="TRAIN",
            profile_name=DL_SCALED_PROFILE,
            feature_catalog=catalog,
        )

        self.assertEqual(artifact.columns["dns_entropy"].strategy, "standard")
        self.assertEqual(artifact.columns["dns_suspicious_tunnel_score"].strategy, "minmax")
        self.assertEqual(artifact.columns["dns_queries_per_window"].strategy, "standard")
        self.assertLessEqual({state.strategy for state in artifact.columns.values()}, {"standard", "minmax"})

    def test_scaled_pyarrow_table_uses_float32_for_scaled_columns(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        artifact = fit_scaling_artifact(
            _train_rows(),
            role="TRAIN",
            profile_name="standard_scaled",
            feature_catalog=catalog,
        )

        table, result = transform_scaling_table(
            pa.table({"dns_entropy": [4.0], "dns_response_code__onehot_noerror": [1]}),
            artifact=artifact,
            role="VALIDATION",
        )

        self.assertEqual(table.schema.field("dns_entropy").type, pa.float32())
        self.assertEqual(result.feature_count, 2)


def _train_rows() -> list[dict[str, object]]:
    return [
        {"dns_entropy": 2.0},
        {"dns_entropy": 4.0},
        {"dns_entropy": 6.0},
    ]


if __name__ == "__main__":
    unittest.main()
