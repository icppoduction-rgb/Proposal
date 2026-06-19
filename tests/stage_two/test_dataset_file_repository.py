from __future__ import annotations

import unittest

from scripts.db.repositories.dataset_file_repository import DatasetFileRepository


class DatasetFileRepositoryBulkRowsTest(unittest.TestCase):
    def test_deduplicate_file_rows_keeps_last_row_per_upsert_key(self) -> None:
        first = {
            "dataset_id": 1,
            "file_path": "sample.log",
            "file_hash_sha256": "old",
        }
        second = {
            "dataset_id": 1,
            "file_path": "sample.log",
            "file_hash_sha256": "new",
        }
        other = {
            "dataset_id": 2,
            "file_path": "sample.log",
            "file_hash_sha256": "other",
        }

        rows = DatasetFileRepository._deduplicate_file_rows([first, second, other])

        self.assertEqual(rows, [second, other])

    def test_chunk_rows_splits_large_batches(self) -> None:
        rows = [{"dataset_id": index, "file_path": f"{index}.log"} for index in range(5)]

        chunks = DatasetFileRepository._chunk_rows(rows, chunk_size=2)

        self.assertEqual(chunks, [rows[:2], rows[2:4], rows[4:]])

    def test_chunk_rows_rejects_non_positive_chunk_size(self) -> None:
        with self.assertRaises(ValueError):
            DatasetFileRepository._chunk_rows([], chunk_size=0)


if __name__ == "__main__":
    unittest.main()
