from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.ingestion.scanner import DatasetFileScanner
from scripts.stage_two.parser_catalog_smoke import (
    EXPECTED_CATALOG_SMOKE_CASES,
    build_catalog_smoke_files,
)


class ParserCatalogSmokeLayoutTest(unittest.TestCase):
    def test_catalog_smoke_cases_match_required_formats(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage-two-catalog-smoke-test-") as directory:
            raw_root = Path(directory) / "raw"
            cases = build_catalog_smoke_files(raw_root, run_id="unit-test")

            self.assertEqual(
                {(case.branch, case.role, case.source_format) for case in cases},
                set(EXPECTED_CATALOG_SMOKE_CASES),
            )

    def test_catalog_smoke_files_are_scanner_compatible(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stage-two-catalog-smoke-test-") as directory:
            raw_root = Path(directory) / "raw"
            build_catalog_smoke_files(raw_root, run_id="unit-test")

            candidates = DatasetFileScanner().scan(raw_root)

            self.assertEqual(len(candidates), len(EXPECTED_CATALOG_SMOKE_CASES))
            self.assertEqual(
                {
                    (candidate.branch, candidate.role, candidate.source_format)
                    for candidate in candidates
                },
                set(EXPECTED_CATALOG_SMOKE_CASES),
            )


if __name__ == "__main__":
    unittest.main()
