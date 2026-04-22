from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from cybersec_platform.contracts.api import DatasetManifest
from cybersec_platform.ml.normalization import NormalizationEngine, target_schema_columns_for_profile


def _build_manifest(file_name: str) -> DatasetManifest:
    return DatasetManifest(
        name="demo",
        source_type="host",
        file_name=file_name,
        required_columns=["feature_a", "feature_b"],
        label_column="label",
        timestamp_column="event_ts",
        entity_id_column="entity_id",
        feature_families=["process"],
    )


@pytest.mark.parametrize(
    ("file_name", "writer"),
    [
        ("sample.csv", lambda frame, path: frame.to_csv(path, index=False)),
        ("sample.tsv", lambda frame, path: frame.to_csv(path, index=False, sep="\t")),
        ("sample.parquet", lambda frame, path: frame.to_parquet(path, index=False)),
        ("sample.xlsx", lambda frame, path: frame.to_excel(path, index=False)),
        ("sample.json", lambda frame, path: frame.to_json(path, orient="records")),
    ],
)
def test_normalization_engine_normalizes_supported_contract_formats(tmp_path: Path, file_name: str, writer):
    raw = tmp_path / file_name
    frame = pd.DataFrame(
        [
            {"entity_id": "host-1", "event_ts": "2026-01-01T00:00:00", "feature_a": 1.0, "feature_b": 2.0, "label": 1},
        ]
    )
    writer(frame, raw)

    output = NormalizationEngine().validate_and_normalize(
        str(raw),
        _build_manifest(file_name),
        str(tmp_path / "normalized.csv"),
        report_path=str(tmp_path / "report.json"),
    )
    assert output.row_count == 1
    assert output.detected_format in {"csv", "tsv", "parquet", "xlsx", "json"}

    normalized = pd.read_csv(output.normalized_path)
    assert "source_type" in normalized.columns
    assert normalized["label"].iloc[0] == 1


def test_target_schema_columns_for_known_profiles():
    columns = target_schema_columns_for_profile("dns_exf_stateful")
    assert "entity_id" in columns
    assert "rr_count" in columns


def test_normalization_engine_accepts_single_json_object(tmp_path: Path):
    raw = tmp_path / "sample.json"
    raw.write_text(
        '{"entity_id":"host-1","event_ts":"2026-01-01T00:00:00Z","feature_a":1.0,"feature_b":2.0,"label":0}',
        encoding="utf-8",
    )

    output = NormalizationEngine().validate_and_normalize(
        str(raw),
        _build_manifest(raw.name),
        str(tmp_path / "normalized.csv"),
        report_path=str(tmp_path / "report.json"),
    )

    normalized = pd.read_csv(output.normalized_path)
    assert output.detected_format == "json"
    assert normalized["entity_id"].iloc[0] == "host-1"
    assert int(normalized["label"].iloc[0]) == 0
