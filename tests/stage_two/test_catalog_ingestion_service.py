from __future__ import annotations

import unittest
from pathlib import Path

from scripts.stage_two.ingestion.catalog_ingestion_service import (
    CatalogIngestionService,
    _deduplicate_candidates_by_resolved_path,
)
from scripts.stage_two.ingestion.scanner import DatasetFileCandidate


class CatalogIngestionConfiguredRootsTest(unittest.TestCase):
    def test_configured_roots_use_filtered_root_only(self) -> None:
        roots = CatalogIngestionService.configured_roots()

        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0][0], "PATH_FOLDER_DATASETS_FILTER")


class CatalogIngestionCandidateDeduplicationTest(unittest.TestCase):
    def test_deduplicate_candidates_keeps_one_row_per_resolved_path(self) -> None:
        first = _candidate(Path("C:/data/dns/TRAIN/csv/a.csv"), "first")
        second = _candidate(Path("C:/data/dns/TRAIN/csv/a.csv"), "second")

        result = _deduplicate_candidates_by_resolved_path([first, second])

        self.assertEqual(result, [second])


def _candidate(path: Path, dataset_name: str) -> DatasetFileCandidate:
    return DatasetFileCandidate(
        path=path,
        root_path=Path("C:/data"),
        relative_path=Path("dns/TRAIN/csv") / path.name,
        dataset_name=dataset_name,
        dataset_slug=dataset_name,
        branch="dns",
        role="TRAIN",
        source_format="csv",
    )


if __name__ == "__main__":
    unittest.main()
