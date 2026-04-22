from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from cybersec_platform.contracts.api import SourceType
from cybersec_platform.ml.auto_training import build_auto_feature_schema_definition, discover_archive_training_inputs, extract_archive


def _build_host_archive(path: Path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("sample.json", '{"exploit": false, "exploit_name": "default", "container": []}')
        archive.writestr(
            "sample.res",
            "timestamp,cpu_usage,memory_usage,network_received\n1631222507.309,0.11,17649664,7532\n",
        )
        archive.writestr(
            "sample.sc",
            "1631222507704076778 0 20940 apache2 20940 select < res=0 exe=apache2\n"
            "1631222507704088918 0 20940 apache2 20940 clone < res=31 exe=apache2 tid=20941 pid=20940\n",
        )


def test_discover_archive_training_inputs_extracts_host_files_and_skips_metadata(tmp_path: Path):
    archive_path = tmp_path / "sample.zip"
    extraction_root = tmp_path / "extracted"
    _build_host_archive(archive_path)

    extracted_files = extract_archive(archive_path, extraction_root)
    assert len(extracted_files) == 3

    discovery = discover_archive_training_inputs(extraction_root, archive_path.name, archive_path)

    assert discovery.source_type is not None
    assert discovery.source_type.value == "host"
    assert len(discovery.trainable_files) == 2
    assert {item.dataset_format for item in discovery.trainable_files} == {"res", "sc"}
    assert all(item.default_label == 0 for item in discovery.trainable_files)
    assert any(item["reason"] == "archive_metadata" for item in discovery.skipped_files)


def test_build_auto_feature_schema_definition_filters_high_cardinality_columns():
    frame = pd.DataFrame(
        {
            "entity_id": ["h-1", "h-2", "h-3", "h-4"],
            "event_ts": [
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:01Z",
                "2026-01-01T00:00:02Z",
                "2026-01-01T00:00:03Z",
            ],
            "source_type": ["host", "host", "host", "host"],
            "label": [0, 1, 0, 1],
            "attack_stage": [None, "exfiltration", None, "exfiltration"],
            "mitre_tactic": ["TA0006", "TA0006", "TA0006", "TA0006"],
            "cpu_usage": [0.1, 0.2, 0.3, 0.4],
            "memory_usage": [100, 120, 110, 130],
            "syscall": ["open", "close", "open", "clone"],
            "raw_args": ["arg-1", "arg-2", "arg-3", "arg-4"],
            "path": ["/tmp/a", "/tmp/b", "/tmp/c", "/tmp/d"],
        }
    )

    schema = build_auto_feature_schema_definition(frame, source_type=SourceType.HOST, name="auto-host-demo")

    assert "cpu_usage" in schema.required_columns
    assert "memory_usage" in schema.required_columns
    assert "syscall" in schema.required_columns
    assert "raw_args" not in schema.required_columns
    assert "path" not in schema.required_columns
    assert "process" in [item.value for item in schema.feature_families]
