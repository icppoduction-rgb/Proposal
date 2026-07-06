from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.extraction.base import NormalizedArtifactInput
from scripts.stage_three.extraction.network_extractors import NETWORK_FEATURES
from scripts.stage_three.extraction.runner import run_host_network_feature_extraction
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.runtime.memory_guard import MemoryGuard


class NetworkFeatureExtractorsTest(unittest.TestCase):
    def test_network_core_groups_extract_and_use_event_order_timing_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_network_artifact(root)

            flow_result = _run_group(root, artifact, "network_flow")
            ports_result = _run_group(root, artifact, "network_ports")
            protocol_result = _run_group(root, artifact, "network_protocol")
            direction_result = _run_group(root, artifact, "network_direction")
            timing_result = _run_group(root, artifact, "network_timing")

            self.assertEqual(flow_result.status, "SUCCESS")
            self.assertEqual(flow_result.runtime_stats["batch_count"], 2)
            flow_rows = _read_rows(flow_result)
            self.assertEqual(flow_rows[0]["network_flow_bytes"], 150.0)
            self.assertEqual(flow_rows[1]["network_flow_bytes"], 150.0)

            port_rows = _read_rows(ports_result)
            self.assertEqual(port_rows[0]["network_dst_port"], 443)
            protocol_rows = _read_rows(protocol_result)
            self.assertIsInstance(protocol_rows[0]["network_transport_protocol"], int)
            direction_rows = _read_rows(direction_result)
            self.assertEqual(direction_rows[0]["network_direction_code"], 1)

            timing_rows = _read_rows(timing_result)
            self.assertEqual(timing_rows[0]["network_flow_duration_ms"], 2.0)
            self.assertEqual(timing_rows[1]["network_flow_duration_ms"], 2.0)
            self.assertEqual(timing_rows[2]["network_flow_duration_ms"], 0.0)

            forbidden = set(timing_result.columns_created).intersection(FORBIDDEN_X_COLUMNS)
            self.assertFalse(forbidden)
            self.assertIn("unsupported_network_column", " ".join(timing_result.warnings))

    def test_network_feature_groups_match_catalog_allow_in_x_columns(self) -> None:
        catalog = load_feature_catalog()
        for feature_group, expected_columns in NETWORK_FEATURES.items():
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
        branch="network",
        role="VALIDATION",
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


def _write_network_artifact(root: Path) -> NormalizedArtifactInput:
    relative_path = Path("parquet") / "normalized" / "network" / "VALIDATION" / "sample.parquet"
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "event_uid": ["net-1", "net-2", "net-3"],
            "event_index": [10, 12, 20],
            "timestamp_type": ["event_order", "event_order", "missing"],
            "event_type": ["network_flow", "network_flow", "network_flow"],
            "source_format": ["netflow_day", "netflow_day", "netflow_day"],
            "flow_id": ["flow-a", "flow-a", "flow-b"],
            "src_ip": ["10.0.0.5", "10.0.0.5", "203.0.113.10"],
            "dst_ip": ["8.8.8.8", "8.8.8.8", "10.0.0.10"],
            "src_port": [53000, 53000, 4444],
            "dst_port": [443, 443, 22],
            "protocol": ["tcp", "tcp", "udp"],
            "features_json": [
                json.dumps({"bytes": 100}),
                json.dumps({"bytes": 50}),
                json.dumps({"bytes": 7}),
            ],
            "raw_fields_json": [
                json.dumps({"flow.bytes": 100}),
                json.dumps({"flow.bytes": 50}),
                json.dumps({"flow.bytes": 7}),
            ],
            "unsupported_network_column": ["no-x", "no-x", "no-x"],
            "label_binary": [0, 0, None],
            "label_family": ["benign", "benign", None],
            "label_subtype": [None, None, None],
            "label_source": ["fixture", "fixture", "none"],
            "label_status": ["explicit_label", "explicit_label", "unlabeled"],
            "label_confidence": [1.0, 1.0, None],
            "label_mapping_rule_id": ["rule-a", "rule-a", None],
        }
    )
    pq.write_table(table, path)
    return NormalizedArtifactInput(
        artifact_id=501,
        dataset_id=601,
        role="VALIDATION",
        branch="network",
        normalized_path=str(relative_path),
        source_format="netflow_day",
        row_count=3,
    )


if __name__ == "__main__":
    unittest.main()
