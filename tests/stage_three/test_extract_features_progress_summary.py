from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from scripts.stage_three.requests import ExtractFeaturesRequest
from scripts.stage_three.reports import console as console_module
from scripts.stage_three.reports.console import StageThreeConsoleReporter


class ExtractFeaturesProgressSummaryTest(unittest.TestCase):
    def test_progress_callback_prints_phase_and_throughput(self) -> None:
        request = ExtractFeaturesRequest(
            command="extract-features",
            branch="host",
            role="TRAIN",
            feature_group="host_syscall",
            verbose=True,
        )
        stdout = StringIO()
        stderr = StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            reporter = StageThreeConsoleReporter(request, storage_root="C:\\storage")
            reporter.progress_callback(
                {
                    "phase": "parquet_write",
                    "status": "end",
                    "artifact_id": 1,
                    "total_artifacts": 2,
                    "rows_read": 1000,
                    "rows_written": 900,
                    "batch_count": 3,
                    "input_bytes": 1024 * 1024,
                    "output_bytes": 1024 * 1024,
                }
            )

        text = stderr.getvalue()
        self.assertIn("phase=parquet_write", text)
        self.assertIn("artifacts=1/2", text)
        self.assertIn("throughput=", text)
        self.assertIn("eta=", text)
        if console_module.psutil is not None:
            self.assertIn("rss_gb=", text)

        summary = reporter.progress_summary()
        self.assertIn("phase_seconds", summary)
        self.assertIn("resource_snapshot", summary)


if __name__ == "__main__":
    unittest.main()
