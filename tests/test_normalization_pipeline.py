import importlib.util
import json
from pathlib import Path
import types
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from normalization.db_writer import DuckDBWriter, DuckDBWriterError
from normalization.dns_normalizer import DNSStatelessNormalizer, DNSStatefulNormalizer
from normalization.host_normalizer import HostWrapper, aggregate_host_wrapper, infer_host_label, infer_host_label_from_path
from normalization.sequence_builder import SequenceBuilder


class NormalizationPipelineTests(unittest.TestCase):
    def test_dns_stateful_normalizer_reads_wrapper_and_encodes_label(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            split_dir = root / "TRAIN"
            split_dir.mkdir(parents=True)
            self._write_json(
                split_dir / "stateful_features-light_audio.json",
                {
                    "data": {
                        "type": "csv",
                        "content": [
                            {
                                "rr": "1",
                                "A_frequency": "2",
                                "NS_frequency": "0",
                                "CNAME_frequency": "0",
                                "SOA_frequency": "0",
                                "NULL_frequency": "0",
                                "PTR_frequency": "0",
                                "HINFO_frequency": "0",
                                "MX_frequency": "0",
                                "TXT_frequency": "0",
                                "AAAA_frequency": "0",
                                "SRV_frequency": "0",
                                "OPT_frequency": "0",
                                "rr_type": "{'A'}",
                                "rr_count": "1",
                                "rr_name_entropy": "0.5",
                                "rr_name_length": "10",
                                "distinct_ns": "1",
                                "distinct_ip": "1",
                                "unique_country": "set()",
                                "unique_asn": "set()",
                                "distinct_domains": "{}",
                                "reverse_dns": "unknown",
                                "a_records": "1",
                                "unique_ttl": "[60]",
                                "ttl_mean": "60",
                                "ttl_variance": "0",
                            }
                        ],
                    }
                },
            )

            normalizer = DNSStatefulNormalizer(root, split="TRAIN", workers=1)
            result = normalizer.run()

            self.assertEqual(result.rows_loaded, 1)
            self.assertEqual(normalizer.normalized_df["label"].iloc[0], "exfiltration")
            self.assertEqual(int(normalizer.normalized_df["label_id"].iloc[0]), 4)
            self.assertIn("rr_type", normalizer.normalized_df.columns)

    def test_dns_stateless_normalizer_creates_ts_column(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            split_dir = root / "TRAIN"
            split_dir.mkdir(parents=True)
            self._write_json(
                split_dir / "stateless_features-light_benign.json",
                {
                    "data": {
                        "type": "csv",
                        "content": [
                            {
                                "timestamp": "2020-01-01 00:00:00",
                                "FQDN_count": "1",
                                "subdomain_length": "2",
                                "upper": "0",
                                "lower": "2",
                                "numeric": "0",
                                "entropy": "1",
                                "special": "0",
                                "labels": "2",
                                "labels_max": "3",
                                "labels_average": "2.5",
                                "longest_word": "4",
                                "sld": "1",
                                "len": "10",
                                "subdomain": "1",
                            }
                        ],
                    }
                },
            )

            normalizer = DNSStatelessNormalizer(root, split="TRAIN", workers=1)
            result = normalizer.run()

            self.assertEqual(result.rows_normalized, 1)
            self.assertIn("ts", normalizer.normalized_df.columns)
            self.assertEqual(int(normalizer.normalized_df["label_id"].iloc[0]), 0)

    def test_dns_stateless_normalizer_reads_mendeley_test_dataset(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            split_dir = root / "TEST"
            split_dir.mkdir(parents=True)
            self._write_json(
                split_dir / "dataset.json",
                {
                    "data": {
                        "type": "csv",
                        "content": [
                            {
                                "column_2": "1624438272607",
                                "column_3": "True",
                                **{f"column_{index}": str(index) for index in range(5, 19)},
                            },
                            {
                                "column_2": "1624438273607",
                                "column_3": "False",
                                **{f"column_{index}": str(index) for index in range(5, 19)},
                            },
                        ],
                    }
                },
            )

            normalizer = DNSStatelessNormalizer(root, split="TEST", workers=1)
            result = normalizer.run()

            self.assertEqual(result.rows_normalized, 2)
            self.assertEqual(normalizer.normalized_df["label"].tolist(), ["exfiltration", "benign"])
            self.assertEqual(normalizer.normalized_df["label_id"].tolist(), [4, 0])
            self.assertIn("ts", normalizer.normalized_df.columns)

    def test_host_label_inference_and_text_aggregation(self) -> None:
        wrapper = HostWrapper(
            path="case1__trace.json",
            label_hint="attack",
            data={
                "type": "text",
                "metadata": {
                    "dataset": "LID-DS 2021",
                    "split": "TRAIN",
                    "relative_path": r"TRAIN\LID-DS 2021\normal_and_attack\case1\case1.sc",
                },
                "content": "1000 1 proc 1 open >\n1010 1 proc 1 read <\n",
            },
        )

        row = aggregate_host_wrapper(wrapper)

        self.assertIsNotNone(row)
        self.assertEqual(row["label"], "attack")
        self.assertEqual(row["event_count"], 2.0)
        self.assertEqual(row["mean_inter_event_gap"], 10.0)

    def test_host_metadata_exploit_maps_to_attack(self) -> None:
        label = infer_host_label(
            {
                "type": "json",
                "metadata": {"dataset": "LID-DS 2021"},
                "content": {"exploit": True},
            }
        )

        self.assertEqual(label, "attack")

    def test_maintainable_log_dataset_is_used_as_benign_host_source(self) -> None:
        label = infer_host_label_from_path(
            relative_path=r"TRAIN\Maintainable Log Dataset\santos\service.log",
            dataset="Maintainable Log Dataset",
        )

        self.assertEqual(label, "benign")

    @unittest.skipIf(importlib.util.find_spec("h5py") is None, "h5py is not installed")
    def test_sequence_builder_writes_hdf5(self) -> None:
        with TemporaryDirectory() as temp_dir:
            frame = pd.DataFrame(
                {
                    "source_file": ["a"] * 4,
                    "timestamp": pd.date_range("2020-01-01", periods=4, freq="s"),
                    "f1": [1.0, 2.0, 3.0, 4.0],
                    "label_id": [0, 0, 1, 1],
                }
            )
            path = SequenceBuilder(window_size=2, stride=1, output_dir=temp_dir).build_from_dataframe(
                frame,
                feature_cols=["f1"],
                label_col="label_id",
                output_name="train_dns",
            )

            import h5py

            with h5py.File(path, "r") as handle:
                self.assertEqual(handle["X"].shape, (3, 2, 1))
                self.assertEqual(handle["y"].shape, (3,))

    @unittest.skipIf(importlib.util.find_spec("duckdb") is None, "duckdb is not installed")
    def test_duckdb_writer_replaces_split_rows(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.duckdb"
            writer = DuckDBWriter(db_path, chunk_size=1)
            try:
                frame = pd.DataFrame(
                    {
                        "id": [1],
                        "source_file": ["a.json"],
                        "dataset": ["unit"],
                        "split": ["TRAIN"],
                        "label": ["attack"],
                        "label_id": [1],
                        "event_count": [1.0],
                        "unique_events": [1.0],
                        "event_entropy": [0.0],
                        "mean_inter_event_gap": [0.0],
                    }
                )
                self.assertEqual(writer.replace_dataframe(frame, "host_features", "TRAIN"), 1)
                self.assertEqual(writer.replace_dataframe(frame, "host_features", "TRAIN"), 1)
                self.assertEqual(writer.table_counts()["host_features"], 1)
            finally:
                writer.close()

    def test_duckdb_writer_lock_error_mentions_stop_command(self) -> None:
        class FakeDuckDBIOException(Exception):
            pass

        def connect(_: str) -> object:
            raise FakeDuckDBIOException("Cannot open file: file is already open")

        fake_duckdb = types.SimpleNamespace(IOException=FakeDuckDBIOException, connect=connect)

        with patch.dict("sys.modules", {"duckdb": fake_duckdb}):
            with self.assertRaises(DuckDBWriterError) as context:
                DuckDBWriter("locked.duckdb")

        message = str(context.exception)
        self.assertIn("python manage.py database duckdb stop", message)
        self.assertIn("cannot open DuckDB database", message)

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
