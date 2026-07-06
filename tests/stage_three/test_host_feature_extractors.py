from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.extraction.base import NormalizedArtifactInput
from scripts.stage_three.extraction.host_extractors import HOST_FEATURES
from scripts.stage_three.extraction.runner import run_host_network_feature_extraction
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.runtime.memory_guard import MemoryGuard


class HostFeatureExtractorsTest(unittest.TestCase):
    def test_host_core_groups_extract_from_normalized_artifact_in_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_host_artifact(root)

            syscall_result = _run_group(root, artifact, "host_syscall")
            process_result = _run_group(root, artifact, "host_process")
            auth_result = _run_group(root, artifact, "host_auth")
            metric_result = _run_group(root, artifact, "host_metrics")

            self.assertEqual(syscall_result.status, "SUCCESS")
            self.assertEqual(syscall_result.rows_read, 3)
            self.assertEqual(syscall_result.rows_written, 3)
            self.assertEqual(syscall_result.runtime_stats["batch_count"], 2)
            self.assertEqual(syscall_result.columns_created, list(HOST_FEATURES["host_syscall"]))
            syscall_table = pq.read_table(syscall_result.output_feature_artifacts[0].parts[0])
            vector = syscall_table.to_pylist()[0]["host_syscall_frequency_vector"]
            self.assertEqual(len(vector), 16)
            self.assertGreater(sum(vector), 0.0)

            process_rows = _read_rows(process_result)
            self.assertIsInstance(process_rows[0]["host_process_name_hash"], int)
            auth_rows = _read_rows(auth_result)
            self.assertEqual(auth_rows[0]["host_auth_failure_flag"], 1)
            metric_rows = _read_rows(metric_result)
            self.assertEqual(metric_rows[2]["host_cpu_load_pct"], 50.0)

            forbidden = set(syscall_result.columns_created).intersection(FORBIDDEN_X_COLUMNS)
            self.assertFalse(forbidden)
            self.assertIn("unsupported_host_column", " ".join(syscall_result.warnings))

    def test_host_feature_groups_match_catalog_allow_in_x_columns(self) -> None:
        catalog = load_feature_catalog()
        for feature_group, expected_columns in HOST_FEATURES.items():
            with self.subTest(feature_group=feature_group):
                catalog_features = {
                    feature["name"]
                    for feature in catalog["feature_groups"][feature_group]["features"]
                    if feature["allow_in_X"]
                }
                self.assertEqual(set(expected_columns), catalog_features)
                self.assertFalse(set(expected_columns).intersection(FORBIDDEN_X_COLUMNS))


def _run_group(root: Path, artifact: NormalizedArtifactInput, feature_group: str):
    return run_host_network_feature_extraction(
        artifacts=[artifact],
        branch="host",
        role="TEST",
        feature_group=feature_group,
        output_root=root / "features",
        storage_root=root,
        batch_rows=2,
        memory_guard=MemoryGuard(
            reserved_ram_gb=8,
            soft_ram_limit_gb=48,
            hard_ram_limit_gb=56,
            psutil_module=False,
        ),
    )


def _read_rows(result):
    tables = [pq.read_table(part) for part in result.output_feature_artifacts[0].parts]
    return [row for table in tables for row in table.to_pylist()]


def _write_host_artifact(root: Path) -> NormalizedArtifactInput:
    relative_path = Path("parquet") / "normalized" / "host" / "TEST" / "sample.parquet"
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "event_uid": ["host-1", "host-2", "host-3"],
            "event_index": [1, 2, 3],
            "timestamp_type": ["event_order", "event_order", "missing"],
            "event_type": ["auth_login_failed", "CreateFileW", "host_metric"],
            "raw_event_name": ["sshd_failed", "CreateFileW", "system.cpu"],
            "source_format": ["auth.log", "bson", "cpu.log"],
            "process_name": ["sshd", "powershell.exe", "metricbeat"],
            "syscall_name": ["ZwAcceptConnectPort", "CreateFileW", None],
            "metric_name": [None, None, "system.cpu.total.norm.pct"],
            "metric_value": [None, None, 0.5],
            "file_path": [None, r"C:\tmp\a.dll", None],
            "features_json": [
                json.dumps({"status": "failed"}),
                json.dumps({"mapped_arguments": {"path": r"C:\tmp\a.dll"}}),
                json.dumps({"system.cpu.total.norm.pct": 0.5}),
            ],
            "raw_fields_json": [
                json.dumps({"message": "failed password"}),
                json.dumps({"MethodName": "CreateFileW"}),
                json.dumps({"metricset.name": "cpu"}),
            ],
            "unsupported_host_column": ["do-not-feature", "do-not-feature", "do-not-feature"],
            "label_binary": [1, 0, None],
            "label_family": ["attack", "benign", None],
            "label_subtype": ["auth", None, None],
            "label_source": ["fixture", "fixture", "none"],
            "label_status": ["explicit_label", "explicit_label", "unlabeled"],
            "label_confidence": [1.0, 1.0, None],
            "label_mapping_rule_id": ["rule-a", "rule-b", None],
        }
    )
    pq.write_table(table, path)
    return NormalizedArtifactInput(
        artifact_id=301,
        dataset_id=401,
        role="TEST",
        branch="host",
        normalized_path=str(relative_path),
        source_format="txt",
        row_count=3,
    )


if __name__ == "__main__":
    unittest.main()
