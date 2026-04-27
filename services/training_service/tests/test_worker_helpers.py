from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path.cwd() / "services" / "training_service"))

from app import worker


def test_prefix_auto_training_entities_rewrites_entity_ids(tmp_path: Path):
    normalized_path = tmp_path / "normalized.csv"
    pd.DataFrame(
        [
            {
                "entity_id": "proc-1",
                "event_ts": "2026-01-01T00:00:00Z",
                "source_type": "host",
                "label": 1,
                "attack_stage": "exfiltration",
                "mitre_tactic": "TA0011",
            }
        ]
    ).to_csv(normalized_path, index=False)

    columns = worker._prefix_auto_training_entities(normalized_path, "archive-one.zip")
    updated = pd.read_csv(normalized_path)

    assert "entity_id" in columns
    assert updated.loc[0, "entity_id"] == "archive-one:proc-1"


def test_build_combined_auto_training_frame_handles_heterogeneous_columns(tmp_path: Path):
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"
    combined_path = tmp_path / "combined.csv"

    pd.DataFrame(
        [
            {
                "entity_id": "archive-a:proc-1",
                "event_ts": "2026-01-01T00:00:00Z",
                "source_type": "host",
                "label": 0,
                "attack_stage": None,
                "mitre_tactic": "TA0006",
                "cpu_usage": 0.1,
            }
        ]
    ).to_csv(first_path, index=False)
    pd.DataFrame(
        [
            {
                "entity_id": "archive-b:proc-2",
                "event_ts": "2026-01-01T00:00:01Z",
                "source_type": "host",
                "label": 1,
                "attack_stage": "exfiltration",
                "mitre_tactic": "TA0011",
                "memory_usage": 128,
            }
        ]
    ).to_csv(second_path, index=False)

    combined_frame, label_distribution = worker._build_combined_auto_training_frame(
        [first_path, second_path],
        combined_path,
    )

    assert combined_path.is_file()
    assert len(combined_frame) == 2
    assert set(["cpu_usage", "memory_usage"]).issubset(set(combined_frame.columns))
    assert label_distribution == {"0": 1, "1": 1}
