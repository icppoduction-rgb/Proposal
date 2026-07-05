from __future__ import annotations

import subprocess
import sys
import unittest
from collections.abc import Callable
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.router_script import router_commands
from scripts.stage_three.cli import router_stage_three


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class StageThreeCliRoutingTest(unittest.TestCase):
    def test_manage_stage_three_help_routes_to_stage_three_parser(self) -> None:
        result = subprocess.run(
            [sys.executable, "manage.py", "stage-three", "--help"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validate-inputs", result.stdout)
        self.assertIn("build-model-ready", result.stdout)

    def test_unknown_stage_three_command_returns_structured_error(self) -> None:
        output, exit_code = _capture_router_exit(
            lambda: router_commands("stage-three", "does-not-exist", None, [])
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("unknown Stage Three command", output)
        self.assertIn("available_commands", output)

    def test_extract_features_request_is_typed_and_normalized(self) -> None:
        with patch("scripts.stage_three.cli.PATH_DATA_STORAGE", "C:\\storage"):
            output = _capture_router(
                lambda: router_stage_three(
                    "extract-features",
                    extra_args=[
                        "--branch",
                        "DNS",
                        "--role",
                        "train",
                        "--feature-group",
                        "dns_lexical",
                        "--experiment-id",
                        "exp001",
                        "--dry-run",
                    ],
                )
            )

        self.assertIn("DRY_RUN", output)
        self.assertIn("stage-three extract-features", output)
        self.assertIn("'branch': 'dns'", output)
        self.assertIn("'role': 'TRAIN'", output)
        self.assertIn("'feature_group': 'dns_lexical'", output)

    def test_missing_path_data_storage_has_clear_error(self) -> None:
        with patch("scripts.stage_three.cli.PATH_DATA_STORAGE", ""):
            output, exit_code = _capture_router_exit(
                lambda: router_stage_three(
                    "build-feature-catalog",
                    extra_args=["--dry-run"],
                )
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("PATH_DATA_STORAGE must be configured", output)

    def test_missing_database_url_has_clear_error_for_db_command(self) -> None:
        with (
            patch("scripts.stage_three.cli.PATH_DATA_STORAGE", "C:\\storage"),
            patch("scripts.stage_three.cli.DATABASE_URL", ""),
        ):
            output, exit_code = _capture_router_exit(
                lambda: router_stage_three(
                    "validate-inputs",
                    extra_args=["--branch", "dns", "--role", "TRAIN"],
                )
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("DATABASE_URL must be configured", output)

    def test_stage_two_routing_still_reaches_stage_two_router(self) -> None:
        output = _capture_router(
            lambda: router_commands("stage-two", "definitely-unknown", None, [])
        )

        self.assertIn("unknown Stage Two command", output)


def _capture_router(callback: Callable[[], None]) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        callback()
    return buffer.getvalue()


def _capture_router_exit(callback: Callable[[], None]) -> tuple[str, int | None]:
    buffer = StringIO()
    exit_code: int | None = None
    with redirect_stdout(buffer):
        try:
            callback()
        except SystemExit as exc:
            exit_code = int(exc.code or 0)
    return buffer.getvalue(), exit_code


if __name__ == "__main__":
    unittest.main()
