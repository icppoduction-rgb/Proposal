from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO

from scripts.stage_three.requests import RunLeakageChecksRequest
from scripts.stage_three.reports.console import (
    BLOCKED_BY_ML_SAFETY,
    StageThreeConsoleReporter,
    leakage_table,
    quality_table,
)


class LeakageConsoleBlockingStatusTest(unittest.TestCase):
    def test_critical_leakage_is_textually_obvious(self) -> None:
        request = RunLeakageChecksRequest(command="run-leakage-checks", experiment_id="exp001")
        checks = [
            {
                "check_group": "leakage",
                "check_name": "x_forbidden_columns",
                "status": "FAIL",
                "severity": "CRITICAL",
                "blocking": True,
                "rows_total": 10,
                "rows_failed": 10,
                "message": "model-ready X contains forbidden leakage columns",
                "details": {"report_path": "C:\\storage\\leakage.md"},
            }
        ]
        output = StringIO()

        with redirect_stdout(output):
            reporter = StageThreeConsoleReporter(request, storage_root="C:\\storage")
            reporter.finish(
                {"status": "FAIL", "checks": checks, "blocked_artifact_ids": [42]},
                summary={"status": "FAIL", "blocking": "yes"},
                tables=[leakage_table(checks), quality_table(checks, title="Leakage Checks")],
                severity="CRITICAL",
            )

        text = output.getvalue()
        self.assertIn("x_forbidden_columns", text)
        self.assertIn("CRITICAL", text)
        self.assertIn(BLOCKED_BY_ML_SAFETY, text)


if __name__ == "__main__":
    unittest.main()
