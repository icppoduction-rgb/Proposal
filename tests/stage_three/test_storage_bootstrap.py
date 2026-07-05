from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.stage_three.storage.bootstrap import (
    BRANCHES,
    ROLES,
    StageThreeStorageBootstrapper,
    bootstrap_stage_three_storage,
)


class StageThreeStorageBootstrapTest(unittest.TestCase):
    def test_bootstrap_creates_required_stage_three_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = bootstrap_stage_three_storage(temp_dir)

            required_paths = {
                Path("reports/ru/stage-three"),
                Path("reports/en/stage-three"),
                Path("logs/stage-three"),
                Path("temp_data/stage_three"),
                Path("parquet/features"),
                Path("parquet/model_ready"),
            }

            for relative_path in required_paths:
                self.assertTrue((Path(temp_dir) / relative_path).is_dir())

            self.assertEqual(result.root, Path(temp_dir))
            self.assertGreaterEqual(len(result.created), len(required_paths))
            self.assertEqual(result.counters["created"], len(result.created))
            self.assertEqual(result.counters["existing"], 0)
            self.assertEqual(result.counters["skipped"], 0)

    def test_bootstrap_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = bootstrap_stage_three_storage(temp_dir)
            second = bootstrap_stage_three_storage(temp_dir)

            self.assertGreater(len(first.created), 0)
            self.assertEqual(second.created, ())
            self.assertEqual(second.skipped, ())
            self.assertEqual(len(second.existing), len(StageThreeStorageBootstrapper.required_relative_paths()))

    def test_bootstrap_creates_role_aware_feature_and_model_ready_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bootstrap_stage_three_storage(temp_dir)

            for branch in BRANCHES:
                for role in ROLES:
                    self.assertTrue((Path(temp_dir) / "parquet" / "features" / branch / role).is_dir())
                    self.assertTrue((Path(temp_dir) / "parquet" / "model_ready" / branch / role).is_dir())

    def test_bootstrap_skips_file_collisions_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            collision = Path(temp_dir) / "logs" / "stage-three"
            collision.parent.mkdir(parents=True)
            collision.write_text("keep this file", encoding="utf-8")

            result = bootstrap_stage_three_storage(temp_dir)

            self.assertIn(collision, result.skipped)
            self.assertEqual(collision.read_text(encoding="utf-8"), "keep this file")

    def test_required_relative_paths_are_unique(self) -> None:
        paths = StageThreeStorageBootstrapper.required_relative_paths()

        self.assertEqual(len(paths), len(set(paths)))


if __name__ == "__main__":
    unittest.main()
