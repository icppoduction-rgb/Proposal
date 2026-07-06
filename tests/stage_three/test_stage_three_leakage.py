from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.quality.common import FAIL
from scripts.stage_three.quality.leakage import (
    LEAKAGE_BLOCKING_STATUS,
    check_model_ready_artifact_for_leakage,
)


class StageThreeLeakageTest(unittest.TestCase):
    def test_catches_known_bad_x_columns_and_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_x_artifact(
                root,
                role="TRAIN",
                rows=[
                    {
                        "dns_query_length": 10,
                        "label_binary": 1,
                        "source_path": r"C:\datasets\raw\dns.csv",
                    }
                ],
            )

            checks = check_model_ready_artifact_for_leakage(artifact, storage_root=root)

        by_name = {check.check_name: check for check in checks}
        self.assertEqual(by_name["x_forbidden_columns"].status, FAIL)
        self.assertTrue(by_name["x_forbidden_columns"].blocking)
        self.assertIn("label_binary", by_name["x_forbidden_columns"].details["forbidden_columns"])
        self.assertIn("source_path", by_name["x_forbidden_columns"].details["forbidden_columns"])
        self.assertEqual(by_name["local_absolute_paths_absent"].status, FAIL)

    def test_detects_test_rows_inside_train_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_x_artifact(
                root,
                role="TRAIN",
                rows=[
                    {"dns_query_length": 10, "dataset_role": "TEST"},
                    {"dns_query_length": 11, "dataset_role": "TRAIN"},
                ],
            )

            checks = check_model_ready_artifact_for_leakage(artifact, storage_root=root)

        test_check = next(check for check in checks if check.check_name == "test_rows_absent_from_train")
        forbidden_check = next(check for check in checks if check.check_name == "x_forbidden_columns")
        self.assertEqual(test_check.status, FAIL)
        self.assertEqual(test_check.leakage_issue_count, 1)
        self.assertEqual(forbidden_check.status, FAIL)

    def test_blocking_status_constant_matches_stage_three_policy(self) -> None:
        self.assertEqual(LEAKAGE_BLOCKING_STATUS, "BLOCKED_BY_LEAKAGE")


def _write_x_artifact(root: Path, *, role: str, rows: list[dict[str, object]]) -> SimpleNamespace:
    path = root / "parquet" / "model_ready" / "exp-leakage" / "dns" / "tree_unscaled" / role / "X.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)
    return SimpleNamespace(
        id=301,
        role=role,
        branch="dns",
        data_type="X",
        artifact_path=path.relative_to(root).as_posix(),
        metadata_json={"experiment_id": "exp-leakage"},
        status="SUCCESS",
    )


if __name__ == "__main__":
    unittest.main()
