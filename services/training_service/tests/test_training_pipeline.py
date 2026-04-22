from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cybersec_platform.contracts.api import DatasetManifest, FeatureSchemaDefinition
from cybersec_platform.ml import training as training_module
from cybersec_platform.ml.training import HybridTrainer


def _feature_schema() -> FeatureSchemaDefinition:
    return FeatureSchemaDefinition(
        name="dns-network-stateful",
        version="1.0.0",
        source_type="network",
        required_columns=["feature_a", "feature_b"],
        canonical_mappings={"event_ts": "event_ts", "entity_id": "entity_id"},
        feature_families=["network_flow"],
    )


def test_training_pipeline_builds_all_branches(tmp_path: Path):
    data = pd.DataFrame(
        [
            {
                "entity_id": f"e-{idx // 10}",
                "event_ts": f"2026-01-01T00:00:{idx:02d}Z",
                "source_type": "network",
                "attack_stage": "exfiltration" if idx % 2 else None,
                "mitre_tactic": "TA0011",
                "feature_a": idx % 2,
                "feature_b": idx,
                "label": idx % 2,
            }
            for idx in range(30)
        ]
    )
    path = tmp_path / "normalized.csv"
    data.to_csv(path, index=False)
    manifest = DatasetManifest(
        name="demo",
        source_type="network",
        file_name="normalized.csv",
        required_columns=["feature_a", "feature_b"],
        label_column="label",
        timestamp_column="event_ts",
        entity_id_column="entity_id",
        feature_families=["network_flow"],
    )
    payload = HybridTrainer().train(str(path), manifest, {"sequence_length": 50, "sequence_stride": 10}, _feature_schema(), reports_dir=str(tmp_path))
    assert {"random_forest", "xgboost", "cnn", "lstm"} <= set(payload["models"].keys())
    assert "f1" in payload["metrics"]
    assert "branch_metrics" in payload["metrics"]


def test_explanation_payload_shape(tmp_path: Path):
    data = pd.DataFrame(
        [
            {
                "entity_id": f"e-{idx // 10}",
                "event_ts": f"2026-01-01T00:00:{idx:02d}Z",
                "source_type": "network",
                "attack_stage": "exfiltration" if idx % 2 else None,
                "mitre_tactic": "TA0011",
                "feature_a": idx % 2,
                "feature_b": idx,
                "label": idx % 2,
            }
            for idx in range(30)
        ]
    )
    path = tmp_path / "normalized.csv"
    data.to_csv(path, index=False)
    manifest = DatasetManifest(
        name="demo",
        source_type="network",
        file_name="normalized.csv",
        required_columns=["feature_a", "feature_b"],
        label_column="label",
        timestamp_column="event_ts",
        entity_id_column="entity_id",
        feature_families=["network_flow"],
    )
    bundle = HybridTrainer().train(str(path), manifest, {"sequence_length": 50, "sequence_stride": 10}, _feature_schema(), reports_dir=str(tmp_path))
    explanation = HybridTrainer().explain_record(bundle, {"feature_a": 1, "feature_b": 7}, top_k=3)
    assert "top_positive" in explanation
    assert "summary" in explanation


def test_explanation_payload_handles_multiclass_shap_tensor(tmp_path: Path, monkeypatch):
    class FakeTreeExplainer:
        def __init__(self, model):
            self.model = model

        def shap_values(self, frame):
            return np.array([[[0.1, 0.9], [0.2, -0.4]]], dtype=float)

    class FakeShapModule:
        TreeExplainer = FakeTreeExplainer

    data = pd.DataFrame(
        [
            {
                "entity_id": f"e-{idx // 10}",
                "event_ts": f"2026-01-01T00:00:{idx:02d}Z",
                "source_type": "network",
                "attack_stage": "exfiltration" if idx % 2 else None,
                "mitre_tactic": "TA0011",
                "feature_a": idx % 2,
                "feature_b": idx,
                "label": idx % 2,
            }
            for idx in range(30)
        ]
    )
    path = tmp_path / "normalized.csv"
    data.to_csv(path, index=False)
    manifest = DatasetManifest(
        name="demo",
        source_type="network",
        file_name="normalized.csv",
        required_columns=["feature_a", "feature_b"],
        label_column="label",
        timestamp_column="event_ts",
        entity_id_column="entity_id",
        feature_families=["network_flow"],
    )
    bundle = HybridTrainer().train(str(path), manifest, {"sequence_length": 50, "sequence_stride": 10}, _feature_schema(), reports_dir=str(tmp_path))
    monkeypatch.setattr(training_module, "shap", FakeShapModule())

    explanation = HybridTrainer().explain_record(bundle, {"feature_a": 1, "feature_b": 7}, top_k=3)

    assert explanation["top_positive"][0]["feature"] == "feature_a"
    assert explanation["top_positive"][0]["contribution"] == 0.9
    assert explanation["top_negative"][0]["feature"] == "feature_b"
    assert explanation["top_negative"][0]["contribution"] == -0.4
