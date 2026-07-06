from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.stage_three.preprocessing.class_balance import (
    BALANCING_NONE,
    BALANCING_RANDOM_OVERSAMPLING,
    BALANCING_RANDOM_UNDERSAMPLING,
    BALANCING_SMOTE,
    TrainOnlyBalancingError,
    balance_split,
    build_class_balance_report,
    compute_class_weight_metadata,
    summarize_class_distribution,
)
from scripts.stage_three.quality.class_balance_report import (
    TASK15_REPORT_FILENAME,
    save_class_balance_reports,
)


class ClassBalanceTest(unittest.TestCase):
    def test_distribution_keeps_missing_labels_separate_from_benign(self) -> None:
        distribution = summarize_class_distribution(_train_rows(), role="TRAIN")

        self.assertEqual(distribution.rows_total, 8)
        self.assertEqual(distribution.class_counts, {"0": 6, "1": 1})
        self.assertEqual(distribution.missing_label_count, 1)
        self.assertEqual(distribution.label_status_distribution["unlabeled"], 1)

    def test_class_weight_and_scale_pos_weight_metadata(self) -> None:
        distribution = summarize_class_distribution(_train_rows(), role="TRAIN")
        metadata = compute_class_weight_metadata(distribution)

        self.assertAlmostEqual(metadata.class_weight["0"], 7 / 12)
        self.assertAlmostEqual(metadata.class_weight["1"], 7 / 2)
        self.assertEqual(metadata.scale_pos_weight, 6.0)
        self.assertEqual(metadata.missing_label_count, 1)

    def test_default_report_does_not_physically_resample(self) -> None:
        result = build_class_balance_report(
            {
                "TRAIN": _train_rows(),
                "VALIDATION": _validation_rows(),
                "TEST": _test_rows(),
            }
        )

        self.assertEqual(result.balancing_method, BALANCING_NONE)
        self.assertFalse(result.splits["TRAIN"].physical_resampling_applied)
        self.assertEqual(result.splits["TRAIN"].rows_before, result.splits["TRAIN"].rows_after)
        self.assertTrue(result.validation_test_not_modified)
        self.assertEqual(result.splits["VALIDATION"].rows_before, result.splits["VALIDATION"].rows_after)
        self.assertEqual(result.splits["TEST"].rows_before, result.splits["TEST"].rows_after)
        self.assertFalse(result.smote_enabled)

    def test_train_only_guard_blocks_validation_and_test_resampling(self) -> None:
        with self.assertRaisesRegex(TrainOnlyBalancingError, "TRAIN"):
            balance_split(_validation_rows(), role="VALIDATION", method=BALANCING_RANDOM_UNDERSAMPLING)
        with self.assertRaisesRegex(TrainOnlyBalancingError, "TRAIN"):
            balance_split(_test_rows(), role="TEST", method=BALANCING_RANDOM_OVERSAMPLING)

    def test_random_undersampling_and_oversampling_apply_only_to_train(self) -> None:
        undersampled = balance_split(
            _train_rows(),
            role="TRAIN",
            method=BALANCING_RANDOM_UNDERSAMPLING,
            random_seed=7,
        )
        oversampled = balance_split(
            _train_rows(),
            role="TRAIN",
            method=BALANCING_RANDOM_OVERSAMPLING,
            random_seed=7,
        )

        self.assertTrue(undersampled.physical_resampling_applied)
        self.assertEqual(undersampled.after_distribution.class_counts, {"0": 1, "1": 1})
        self.assertEqual(undersampled.after_distribution.missing_label_count, 1)
        self.assertTrue(oversampled.physical_resampling_applied)
        self.assertEqual(oversampled.after_distribution.class_counts, {"0": 6, "1": 6})

    def test_smote_requires_explicit_flag_and_is_warning_only_in_mvp(self) -> None:
        with self.assertRaisesRegex(ValueError, "enable_smote=True"):
            balance_split(_train_rows(), role="TRAIN", method=BALANCING_SMOTE)

        result = balance_split(
            _train_rows(),
            role="TRAIN",
            method=BALANCING_SMOTE,
            enable_smote=True,
        )

        self.assertTrue(result.smote_enabled)
        self.assertFalse(result.physical_resampling_applied)
        self.assertEqual(result.rows_before, result.rows_after)
        self.assertTrue(any("SMOTE" in warning for warning in result.warnings))

    def test_report_contains_required_task15_sections(self) -> None:
        result = build_class_balance_report(
            {
                "TRAIN": _train_rows(),
                "VALIDATION": _validation_rows(),
                "TEST": _test_rows(),
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_class_balance_reports(result)

            report = root / "en" / TASK15_REPORT_FILENAME
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")

        self.assertIn("Task14-scaling-profiles-and-preprocessing-artifacts.md", text)
        self.assertIn("Before/After Class Distribution", text)
        self.assertIn("Balancing method", text)
        self.assertIn("VALIDATION/TEST not modified", text)
        self.assertIn("scale_pos_weight", text)
        self.assertIn("en", written.report_paths)


def _train_rows() -> list[dict[str, object]]:
    return [
        {"sample_uid": "tr-0", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-1", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-2", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-3", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-4", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-5", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-6", "label_binary": 1, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "tr-7", "label_binary": None, "label_status": "unlabeled", "label_source": "none"},
    ]


def _validation_rows() -> list[dict[str, object]]:
    return [
        {"sample_uid": "val-0", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "val-1", "label_binary": 1, "label_status": "explicit_label", "label_source": "manual"},
    ]


def _test_rows() -> list[dict[str, object]]:
    return [
        {"sample_uid": "te-0", "label_binary": 0, "label_status": "explicit_label", "label_source": "manual"},
        {"sample_uid": "te-1", "label_binary": None, "label_status": "unlabeled", "label_source": "none"},
    ]


if __name__ == "__main__":
    unittest.main()
