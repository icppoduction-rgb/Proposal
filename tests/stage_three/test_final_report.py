from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.stage_three.reports.final_report import (
    DOCUMENTATION_FILES,
    FinalStageThreeReportResult,
    TASK20_PREVIOUS_REPORT_PATH,
    TASK20_REPORT_FILENAME,
    save_final_stage_three_reports,
)


class FinalStageThreeReportTest(unittest.TestCase):
    def test_save_final_report_writes_ru_and_en_with_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = _result(root)

            written = save_final_stage_three_reports(result)

            ru_report = root / "ru" / TASK20_REPORT_FILENAME
            en_report = root / "en" / TASK20_REPORT_FILENAME
            self.assertTrue(ru_report.exists())
            self.assertTrue(en_report.exists())
            text = en_report.read_text(encoding="utf-8")

        self.assertIn(TASK20_PREVIOUS_REPORT_PATH, text)
        self.assertIn("Final report path", text)
        self.assertIn("Documentation Created/Updated", text)
        self.assertIn("Stage Four readiness status", text)
        self.assertIn("NOT_READY_FOR_STAGE_FOUR", text)
        self.assertIn("Machine-readable Details", text)
        self.assertIn("docs/en/stage-three/usage_guide.md", text)
        self.assertEqual(written.report_paths["en"], str(en_report))


def _result(root: Path) -> FinalStageThreeReportResult:
    return FinalStageThreeReportResult(
        status="PARTIAL_SUCCESS",
        stage_four_readiness_status="NOT_READY_FOR_STAGE_FOUR",
        experiment_id="exp-final",
        branch="dns",
        previous_report_path=TASK20_PREVIOUS_REPORT_PATH,
        report_paths={
            "ru": str(root / "ru" / TASK20_REPORT_FILENAME),
            "en": str(root / "en" / TASK20_REPORT_FILENAME),
        },
        documentation_files=list(DOCUMENTATION_FILES),
        feature_catalog_summary={"version": "1.0"},
        stage_two_inputs_summary={"linked_normalized_artifact_count": 1},
        feature_extraction_summary={"feature_artifact_count": 1},
        label_alignment_summary={"y_artifact_count": 1},
        separation_summary={"x_artifact_count": 1},
        preprocessing_summary={"profiles": ["tree_unscaled"]},
        class_balance_summary={"validation_test_balancing_allowed": False},
        sequence_artifact_summary={"sequence_artifact_count": 0},
        model_ready_artifact_summary={"artifact_count": 1},
        quality_checks_summary={"report_count": 0},
        leakage_checks_summary={"report_count": 0},
        traceability_checks_summary={"report_count": 0},
        runtime_summary={"default_profile": "balanced"},
        known_limitations=["No production checks were provided."],
        readiness_blockers=["Missing final quality/leakage/traceability check groups."],
    )


if __name__ == "__main__":
    unittest.main()
