from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.stage_two.parser_coverage import (
    ParserCoverageResult,
    ParserCoverageRow,
    _stage_one_counts_from_payload,
)
from scripts.stage_two.reports.parser_reports import save_parser_coverage_reports


class ParserCoverageTest(unittest.TestCase):
    def test_stage_one_counts_from_role_format_payload(self) -> None:
        payload = {
            "TRAIN": {"csv": ["a.csv", "b.csv"], "pcap": ["a.pcap"]},
            "VALIDATION": {"txt": ["domains.txt"]},
        }

        counts = _stage_one_counts_from_payload(payload)

        self.assertEqual(
            counts,
            [
                {"role": "TRAIN", "source_format": "csv", "files_count": 2},
                {"role": "TRAIN", "source_format": "pcap", "files_count": 1},
                {"role": "VALIDATION", "source_format": "txt", "files_count": 1},
            ],
        )

    def test_save_parser_coverage_reports_writes_required_files(self) -> None:
        result = ParserCoverageResult(
            status="SUCCESS",
            branch_filter="dns",
            summary={
                "matrix_rows": 1,
                "catalog_files": 2,
                "catalog_gap_rows": 0,
            },
            matrix=(
                ParserCoverageRow(
                    branch="dns",
                    role="TRAIN",
                    source_format="csv",
                    files_count=2,
                    parser_active=True,
                    parser_class="DnsCsvParser",
                    parser_name="dns_csv_parser",
                    parser_version="v1",
                    registry_is_active=True,
                    supported_role=None,
                    action="ready_for_normalization",
                    diagnostics=(),
                ),
            ),
            stage_one_diagnostics={},
            report_paths={},
        )
        with TemporaryDirectory() as tmp:
            paths = save_parser_coverage_reports(asdict(result), storage_root=tmp)

            self.assertEqual(
                set(paths),
                {"en_json", "ru_json", "en_md", "ru_md"},
            )
            for relative_path in paths.values():
                self.assertTrue((Path(tmp) / relative_path).exists())

            en_payload = json.loads((Path(tmp) / paths["en_json"]).read_text(encoding="utf-8"))
            self.assertEqual(en_payload["matrix"][0]["parser_class"], "DnsCsvParser")


if __name__ == "__main__":
    unittest.main()
