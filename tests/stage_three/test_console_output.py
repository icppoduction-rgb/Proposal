from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

from scripts.stage_three.cli import _extract_bottleneck_summary, _model_ready_console_summary
from scripts.stage_three.requests import ValidateInputsRequest
from scripts.stage_three.reports.console import ConsoleTable, StageThreeConsoleReporter


class StageThreeConsoleOutputTest(unittest.TestCase):
    def test_success_summary_renders_header_and_report_path(self) -> None:
        request = ValidateInputsRequest(command="validate-inputs", branch="dns", role="TRAIN")
        output = StringIO()

        with redirect_stdout(output):
            reporter = StageThreeConsoleReporter(request, storage_root="C:\\storage")
            reporter.start()
            reporter.finish(
                {"status": "SUCCESS", "report_paths": {"en": "C:\\storage\\report.md"}},
                summary={"status": "SUCCESS", "report_paths": {"en": "C:\\storage\\report.md"}},
            )

        text = output.getvalue()
        self.assertIn("Stage Three validate-inputs", text)
        self.assertIn("Status", text)
        self.assertIn("report_paths", text)

    def test_partial_success_table_renders_blocking_column(self) -> None:
        request = ValidateInputsRequest(command="validate-inputs", branch="dns", role="TRAIN")
        output = StringIO()

        with redirect_stdout(output):
            reporter = StageThreeConsoleReporter(request, storage_root="C:\\storage")
            reporter.finish(
                {"status": "PARTIAL_SUCCESS"},
                summary={"status": "PARTIAL_SUCCESS"},
                tables=[
                    ConsoleTable(
                        "Checks",
                        ["check_name", "status", "blocking"],
                        [["sample_check", "WARN", "no"]],
                    )
                ],
            )

        text = output.getvalue()
        self.assertIn("PARTIAL_SUCCESS", text)
        self.assertIn("sample_check", text)
        self.assertIn("blocking", text)

    def test_failure_summary_mentions_phase_and_missing_report(self) -> None:
        request = ValidateInputsRequest(command="validate-inputs", branch="dns", role="TRAIN")
        output = StringIO()

        with redirect_stdout(output):
            reporter = StageThreeConsoleReporter(request, storage_root="C:\\storage")
            reporter.error(phase="catalog_lookup", error="database unavailable")

        text = output.getvalue()
        self.assertIn("Status: ERROR", text)
        self.assertIn("phase: catalog_lookup", text)
        self.assertIn("report: not written", text)

    def test_bottleneck_summary_uses_phase_percentages(self) -> None:
        result = SimpleNamespace(runtime_stats={"batch_count": 1}, resume_skipped_count=0)
        summary = _extract_bottleneck_summary(
            result,
            {
                "phase_seconds": {
                    "catalog_lookup": 1.0,
                    "feature_compute": 3.0,
                    "parquet_write": 6.0,
                }
            },
        )

        self.assertIn("write 60%", summary)
        self.assertIn("compute 30%", summary)
        self.assertIn("DB 10%", summary)

    def test_model_ready_summary_reports_dropped_columns(self) -> None:
        role_result = SimpleNamespace(
            role="TRAIN",
            source_feature_artifact_ids=[1],
            artifacts=[
                SimpleNamespace(
                    role="TRAIN",
                    data_type="X",
                    artifact_path="C:\\storage\\X.parquet",
                )
            ],
            x_row_count=10,
            y_row_count=10,
            feature_count=2,
            target_distribution={"0": 7, "1": 3},
            x_columns=["feature_a", "feature_b"],
            feature_group="host_syscall",
            dropped_columns=[{"name": "label_binary", "reason": "forbidden in X"}],
        )
        result = SimpleNamespace(
            status="SUCCESS",
            roles=["TRAIN"],
            role_results=[role_result],
            preprocessing_profile="tree_unscaled",
            split_index_artifact=None,
            preprocessing_metadata_artifact=None,
            feature_count=2,
            warnings=[],
            report_paths={},
        )

        summary = _model_ready_console_summary(result)

        self.assertEqual(summary["feature_groups_included"], ["host_syscall"])
        self.assertEqual(summary["excluded_forbidden_columns_count"], 1)
        self.assertEqual(summary["skipped_columns"], ["label_binary: forbidden in X"])
        self.assertIn("missing roles: TEST, VALIDATION", summary["warnings"])


if __name__ == "__main__":
    unittest.main()
