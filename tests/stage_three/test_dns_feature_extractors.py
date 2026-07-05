from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.extraction.base import NormalizedArtifactInput
from scripts.stage_three.extraction.dns_extractors import (
    DNS_MVP_FEATURES,
    LABEL_COLUMNS,
    TRACEABILITY_COLUMNS,
)
from scripts.stage_three.extraction.runner import run_dns_feature_extraction
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.runtime.memory_guard import MemoryGuard


class DnsFeatureExtractorsMvpTest(unittest.TestCase):
    def test_dns_lexical_features_are_extracted_from_sample_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_sample_normalized_artifact(root)

            result = _run_group(root, artifact, "dns_lexical")

            self.assertEqual(result.status, "SUCCESS")
            self.assertEqual(result.rows_read, 3)
            self.assertEqual(result.rows_written, 3)
            self.assertEqual(result.columns_created, list(DNS_MVP_FEATURES["dns_lexical"]))
            table = pq.read_table(result.output_feature_artifacts[0].parts[0])
            rows = table.to_pylist()
            self.assertEqual(rows[0]["dns_query_length"], len("a1-b2.long.example.com"))
            self.assertEqual(rows[0]["dns_label_count"], 4)
            self.assertEqual(rows[0]["dns_digit_count"], 2)
            self.assertEqual(rows[0]["dns_special_char_count"], 1)
            self.assertTrue(rows[2]["sample_uid"].startswith("na:101:event:event-3"))
            self.assertIsNone(rows[2]["label_binary"])
            self.assertEqual(rows[2]["label_status"], "unlabeled")

    def test_dns_entropy_feature_matches_catalog_and_has_no_forbidden_x_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_sample_normalized_artifact(root)

            result = _run_group(root, artifact, "dns_entropy")

            table = pq.read_table(result.output_feature_artifacts[0].parts[0])
            x_columns = set(result.columns_created)
            self.assertEqual(x_columns, {"dns_entropy"})
            self.assertGreater(table.column("dns_entropy")[0].as_py(), 0.0)
            self.assertFalse(x_columns.intersection(FORBIDDEN_X_COLUMNS))
            self.assertTrue(set(TRACEABILITY_COLUMNS).issubset(table.column_names))
            self.assertTrue(set(LABEL_COLUMNS).issubset(table.column_names))
            catalog = load_feature_catalog()
            catalog_features = {
                feature["name"]
                for feature in catalog["feature_groups"]["dns_entropy"]["features"]
                if feature["allow_in_X"]
            }
            self.assertEqual(x_columns, catalog_features)

    def test_dns_temporal_features_are_written_with_missing_ratios(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = _write_sample_normalized_artifact(root)

            result = _run_group(root, artifact, "dns_temporal")

            self.assertEqual(result.columns_created, list(DNS_MVP_FEATURES["dns_temporal"]))
            self.assertEqual(result.missing_ratios["dns_queries_per_window"], 0.0)
            self.assertEqual(result.missing_ratios["dns_burst_score"], 0.0)
            table = pq.read_table(result.output_feature_artifacts[0].parts[0])
            rows = table.to_pylist()
            self.assertEqual(rows[0]["dns_queries_per_window"], 2)
            self.assertEqual(rows[1]["dns_queries_per_window"], 2)
            self.assertEqual(rows[2]["dns_queries_per_window"], 1)
            self.assertGreaterEqual(rows[1]["dns_burst_score"], 0.0)


def _run_group(root: Path, artifact: NormalizedArtifactInput, feature_group: str):
    return run_dns_feature_extraction(
        artifacts=[artifact],
        branch="dns",
        role="TRAIN",
        feature_group=feature_group,
        output_root=root / "features",
        storage_root=root,
        batch_rows=10,
        memory_guard=MemoryGuard(
            reserved_ram_gb=8,
            soft_ram_limit_gb=48,
            hard_ram_limit_gb=56,
            psutil_module=False,
        ),
    )


def _write_sample_normalized_artifact(root: Path) -> NormalizedArtifactInput:
    relative_path = Path("parquet") / "normalized" / "dns" / "TRAIN" / "sample.parquet"
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "event_uid": ["event-1", "event-2", "event-3"],
            "event_timestamp": [
                datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 0, 1, 5, tzinfo=timezone.utc),
            ],
            "event_order": [1, 2, 3],
            "domain": ["a1-b2.long.example.com", "x.example.com", "missing-label.test"],
            "label_binary": [1, 0, None],
            "label_family": ["exfil", "benign", None],
            "label_subtype": ["dns_tunnel", None, None],
            "label_source": ["fixture", "fixture", "none"],
            "label_status": ["explicit_label", "explicit_label", "unlabeled"],
            "label_confidence": [1.0, 1.0, None],
            "label_mapping_rule_id": ["rule-1", "rule-2", None],
        }
    )
    pq.write_table(table, path)
    return NormalizedArtifactInput(
        artifact_id=101,
        dataset_id=202,
        role="TRAIN",
        branch="dns",
        normalized_path=str(relative_path),
        source_format="parquet",
        row_count=3,
    )


if __name__ == "__main__":
    unittest.main()
