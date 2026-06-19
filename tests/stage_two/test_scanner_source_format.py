from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.stage_two.ingestion.scanner import DatasetFileScanner


LISTED_SOURCE_FORMATS: tuple[str, ...] = (
    "auth.log",
    "cpu.log",
    "diskio.log",
    "filesystem.log",
    "fsstat.log",
    "journal~",
    "json-1",
    "log-1",
    "log-2",
    "log-3",
    "mail-info-1",
    "mail-warn-1",
    "mainlog-1",
    "mainlog-2",
    "mainlog-3",
    "messages-1",
    "netflow_day",
    "netflow_ids",
    "pcap.csv",
    "process.summary.log",
    "socket.summary.log",
    "syslog-1",
    "syslog-2",
    "syslog-3",
    "syslog-4",
    "syslog.log",
    "wls_day",
)


class DatasetFileScannerSourceFormatTest(unittest.TestCase):
    def test_sorted_tree_bucket_format_wins_for_listed_formats(self) -> None:
        scanner = DatasetFileScanner()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source_format in LISTED_SOURCE_FORMATS:
                bucket = root / "host" / "TRAIN" / source_format
                bucket.mkdir(parents=True, exist_ok=True)
                (bucket / "sample.raw").write_text("x", encoding="utf-8")

            candidates = scanner.scan(root)

        found = {
            candidate.relative_path.parts[-2]: candidate.source_format
            for candidate in candidates
        }
        for source_format in LISTED_SOURCE_FORMATS:
            self.assertEqual(found[source_format], source_format)

    def test_raw_filename_heuristic_preserves_compound_names(self) -> None:
        scanner = DatasetFileScanner()

        for source_format in LISTED_SOURCE_FORMATS:
            with self.subTest(source_format=source_format):
                self.assertEqual(
                    scanner.infer_source_format(Path(f"sample.{source_format}")),
                    source_format,
                )

    def test_bucket_overrides_generic_file_extension(self) -> None:
        scanner = DatasetFileScanner()

        self.assertEqual(
            scanner.infer_source_format(
                Path("sample.csv"),
                relative_path=Path("host/TRAIN/pcap.csv/sample.csv"),
            ),
            "pcap.csv",
        )
        self.assertEqual(
            scanner.infer_source_format(
                Path("sample.log"),
                relative_path=Path("host/TRAIN/process.summary.log/sample.log"),
            ),
            "process.summary.log",
        )

    def test_experiments_and_unroled_paths_are_not_catalog_candidates(self) -> None:
        scanner = DatasetFileScanner()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dns" / "TRAIN" / "csv").mkdir(parents=True)
            (root / "dns" / "TRAIN" / "csv" / "train.csv").write_text("x", encoding="utf-8")
            (root / "dns" / "EXPERIMENTS" / "csv").mkdir(parents=True)
            (root / "dns" / "EXPERIMENTS" / "csv" / "experiment.csv").write_text(
                "x",
                encoding="utf-8",
            )
            (root / "dns" / "misc").mkdir(parents=True)
            (root / "dns" / "misc" / "unknown.csv").write_text("x", encoding="utf-8")

            candidates = scanner.scan(root)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].role, "TRAIN")


if __name__ == "__main__":
    unittest.main()
