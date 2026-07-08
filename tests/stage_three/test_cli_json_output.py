from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class StageThreeCliJsonOutputTest(unittest.TestCase):
    def test_dry_run_json_is_single_automation_object(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "manage.py",
                "stage-three",
                "extract-features",
                "--branch",
                "dns",
                "--role",
                "TRAIN",
                "--feature-group",
                "dns_lexical",
                "--dry-run",
                "--json",
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "stage-three extract-features")
        self.assertEqual(payload["status"], "DRY_RUN")
        self.assertIn("artifact_paths", payload)
        self.assertIn("report_paths", payload)
        self.assertIn("warnings", payload)
        self.assertIn("blocking_issues", payload)
        self.assertEqual(result.stdout.count("\n"), 1)


if __name__ == "__main__":
    unittest.main()
