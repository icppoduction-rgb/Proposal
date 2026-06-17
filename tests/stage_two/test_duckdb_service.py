from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from scripts.stage_two.duckdb.service import DuckDBAnalyticsService, REQUIRED_COLUMNS


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


if __name__ == "__main__":
    unittest.main()
