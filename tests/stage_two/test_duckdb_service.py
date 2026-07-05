from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_two.duckdb.service import DuckDBAnalyticsService, DuckDBRuntimeSettings, REQUIRED_COLUMNS


class DuckDBAnalyticsServiceTest(unittest.TestCase):
    def test_empty_parquet_views_keep_required_columns(self) -> None:
        with TemporaryDirectory() as directory:
            service = DuckDBAnalyticsService(storage_root=directory, database_path=":memory:")
            connection = service.connect()
            try:
                service.create_views(connection)
                for view_name, required_columns in REQUIRED_COLUMNS.items():
                    columns = set(service._columns(connection, view_name))
                    self.assertTrue(set(required_columns).issubset(columns), view_name)
                    row_count = connection.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
                    self.assertEqual(row_count, 0, view_name)
            finally:
                connection.close()

    def test_connect_applies_bounded_runtime_settings(self) -> None:
        with TemporaryDirectory() as directory:
            service = DuckDBAnalyticsService(
                storage_root=directory,
                database_path=":memory:",
                runtime_settings=DuckDBRuntimeSettings(
                    memory_limit="1GB",
                    threads=2,
                    temp_directory=Path(directory) / "duckdb-spill",
                    max_temp_directory_size="2GB",
                ),
            )
            connection = service.connect()
            try:
                self.assertEqual(connection.execute("SELECT current_setting('threads')").fetchone()[0], 2)
                temp_directory = connection.execute("SELECT current_setting('temp_directory')").fetchone()[0]
                self.assertIn("duckdb-spill", temp_directory)
            finally:
                connection.close()

    def test_run_checks_emits_progress_events(self) -> None:
        events: list[str] = []
        with TemporaryDirectory() as directory:
            service = DuckDBAnalyticsService(
                storage_root=directory,
                database_path=":memory:",
                progress_callback=lambda event, payload: events.append(event),
            )
            service.run_checks()
        self.assertIn("run_started", events)
        self.assertEqual(events.count("view_finished"), 3)
        self.assertIn("check_finished", events)
        self.assertIn("report_finished", events)

    def test_run_checks_uses_streaming_metadata_for_parquet_layers(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_parquet(
                root / "parquet" / "normalized" / "dns" / "TRAIN" / "events" / "sample" / "schema=v1" / "part.parquet",
                [
                    {
                        "event_uid": "event-1",
                        "dataset_role": "TRAIN",
                        "branch": "dns",
                        "source_file_path": "raw.csv",
                    }
                ],
            )
            self._write_parquet(
                root / "parquet" / "features" / "dns_features" / "TRAIN" / "sample" / "schema=v1" / "part.parquet",
                [{"role": "TRAIN", "branch": "dns", "feature_group": "dns_features"}],
            )
            self._write_parquet(
                root / "parquet" / "model_ready" / "tabular" / "dns" / "TRAIN" / "schema=v1" / "X_train.parquet",
                [{"role": "TRAIN", "dataset_role": "TRAIN", "sample_uid": "sample-1"}],
            )

            service = DuckDBAnalyticsService(storage_root=root, database_path=":memory:")
            report = service.run_checks()

        self.assertEqual(report.status, "SUCCESS")
        row_count_checks = {check.check_name: check for check in report.checks if check.check_name.startswith("row_counts_")}
        self.assertEqual(row_count_checks["row_counts_normalized_all"].rows_total, 1)
        self.assertEqual(row_count_checks["row_counts_features_all"].rows_total, 1)
        self.assertEqual(row_count_checks["row_counts_model_ready_all"].rows_total, 1)

    def _write_parquet(self, path: Path, rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist(rows), path)


if __name__ == "__main__":
    unittest.main()
