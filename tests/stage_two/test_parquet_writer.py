from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq

from scripts.stage_two.parquet.writer import ParquetArtifactWriter


class ParquetArtifactWriterTest(unittest.TestCase):
    def test_json_fields_are_serialized_before_arrow_type_inference(self) -> None:
        rows = [
            {
                "event_uid": "one",
                "raw_fields_json": {"mixed": 1, "items": [1, "two"]},
                "metadata_json": {"ttl_mean": 3.5},
            },
            {
                "event_uid": "two",
                "raw_fields_json": {"mixed": "not-a-number", "items": ["x"]},
                "metadata_json": {"ttl_mean": " 21:07:56.450015"},
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            writer = ParquetArtifactWriter(Path(directory))
            result = writer.write_normalized(
                rows,
                branch="dns",
                role="TRAIN",
                modality="dns",
                dataset_slug="mixed-json-smoke",
                schema_version="v1",
                run_id="test",
            )

            table = pq.read_table(result.absolute_path)
            payload = table.to_pylist()

        self.assertEqual(result.row_count, 2)
        self.assertIsInstance(payload[0]["raw_fields_json"], str)
        self.assertEqual(json.loads(payload[0]["raw_fields_json"])["mixed"], 1)
        self.assertEqual(json.loads(payload[1]["raw_fields_json"])["mixed"], "not-a-number")
        self.assertEqual(
            json.loads(payload[1]["metadata_json"])["ttl_mean"],
            " 21:07:56.450015",
        )


if __name__ == "__main__":
    unittest.main()
