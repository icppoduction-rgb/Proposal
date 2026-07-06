from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.report import (
    TASK14_REPORT_FILENAME,
    save_scaling_profile_reports,
)
from scripts.stage_three.preprocessing.scaling import (
    fit_scaling_artifact,
    register_scaling_preprocessing_artifact,
    transform_scaling,
    write_scaling_artifact_json,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"


class PreprocessingArtifactRegistrationTest(unittest.TestCase):
    def test_registers_train_fitted_scaling_artifact(self) -> None:
        artifact = fit_scaling_artifact(
            [{"dns_entropy": 2.0}, {"dns_entropy": 4.0}, {"dns_entropy": 6.0}],
            role="TRAIN",
            profile_name="standard_scaled",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "scaler.json"
            persisted = write_scaling_artifact_json(artifact, artifact_path)
            repository = FakePreprocessingRepository()
            catalog_artifact, summary = register_scaling_preprocessing_artifact(
                repository,
                persisted,
                branch="dns",
                feature_group="dns_entropy",
                artifact_path=artifact_path,
                fitted_on_feature_artifact_id=101,
            )

        self.assertEqual(catalog_artifact.id, 8101)
        self.assertEqual(summary.preprocessing_artifact_ids, [8101])
        self.assertEqual(repository.registered_values[0]["fitted_on_role"], "TRAIN")
        self.assertEqual(repository.registered_values[0]["preprocessing_type"], "scaler:standard_scaled")
        self.assertEqual(repository.registered_values[0]["fitted_on_feature_artifact_id"], 101)
        self.assertEqual(repository.registered_values[0]["columns_json"]["scaled_columns"], ["dns_entropy"])
        self.assertIn("statistics_path", repository.registered_values[0]["params_json"]["metadata"])

    def test_registration_rejects_non_train_fit_role(self) -> None:
        artifact = fit_scaling_artifact(
            [{"dns_entropy": 2.0}, {"dns_entropy": 4.0}],
            role="TRAIN",
            profile_name="standard_scaled",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )
        invalid = replace(artifact, fit_role="TEST")

        with self.assertRaisesRegex(ValueError, "TRAIN"):
            register_scaling_preprocessing_artifact(
                FakePreprocessingRepository(),
                invalid,
                branch="dns",
                artifact_path="scaler.json",
            )

    def test_task14_report_includes_required_sections(self) -> None:
        artifact = fit_scaling_artifact(
            [{"dns_entropy": 2.0}, {"dns_entropy": 4.0}, {"dns_entropy": 6.0}],
            role="TRAIN",
            profile_name="standard_scaled",
            feature_catalog=load_feature_catalog(DEFAULT_CATALOG_PATH),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_path = root / "artifacts" / "scaler.json"
            persisted = write_scaling_artifact_json(artifact, artifact_path)
            result = transform_scaling([{"dns_entropy": 4.0}], artifact=persisted, role="VALIDATION")
            repository = FakePreprocessingRepository()
            _, summary = register_scaling_preprocessing_artifact(
                repository,
                persisted,
                branch="dns",
                artifact_path=artifact_path,
            )

            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_scaling_profile_reports(result, registration_summary=summary)

            report = root / "en" / TASK14_REPORT_FILENAME
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")

        self.assertIn("Task13-missing-values-and-categorical-encoding.md", text)
        self.assertIn("Scaling Profiles Created", text)
        self.assertIn("Fit role", text)
        self.assertIn("8101", text)
        self.assertIn("Feature Count Per Profile", text)
        self.assertIn("Scaler statistics location", text)
        self.assertIn("en", written.report_paths)


class FakePreprocessingRepository:
    def __init__(self) -> None:
        self.registered_values: list[dict[str, Any]] = []

    def register_preprocessing_artifact(self, **values: Any) -> SimpleNamespace:
        self.registered_values.append(values)
        return SimpleNamespace(id=8100 + len(self.registered_values), **values)


if __name__ == "__main__":
    unittest.main()
