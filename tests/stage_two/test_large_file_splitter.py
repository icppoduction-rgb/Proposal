from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.cli import _parse_split_large_files_args
from scripts.stage_two.splitting.large_files import _split_line_file


class LargeFileSplitterTest(unittest.TestCase):
    def test_split_line_file_preserves_lines_and_repeats_header(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="large-file-splitter-"))
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        source = directory / "dataset.csv"
        source.write_text("a,b\n1,2\n3,4\n5,6\n7,8\n", encoding="utf-8")

        chunks = _split_line_file(
            source,
            output_dir=directory / "parts",
            max_part_size_bytes=8,
            has_header=True,
            overwrite=False,
        )

        self.assertGreater(len(chunks), 1)
        payloads = [chunk.path.read_text(encoding="utf-8") for chunk in chunks]
        self.assertEqual(payloads[0], "a,b\n1,2\n")
        self.assertTrue(all(payload.startswith("a,b\n") for payload in payloads))
        data_lines = [
            line
            for payload in payloads
            for line in payload.splitlines()
            if line != "a,b"
        ]
        self.assertEqual(data_lines, ["1,2", "3,4", "5,6", "7,8"])

    def test_parse_split_large_files_args(self) -> None:
        request = _parse_split_large_files_args(
            [
                "--branch",
                "DNS",
                "--role",
                "test",
                "--format",
                "csv",
                "--limit",
                "2",
                "--max-part-size-mb",
                "512",
                "--min-size-mb",
                "64",
                "--header",
                "no",
                "--apply",
                "--register",
            ]
        )

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.role, "TEST")
        self.assertEqual(request.source_format, "csv")
        self.assertEqual(request.limit, 2)
        self.assertEqual(request.max_part_size_bytes, 512 * 1024 * 1024)
        self.assertEqual(request.min_file_size_bytes, 64 * 1024 * 1024)
        self.assertEqual(request.header_mode, "no")
        self.assertTrue(request.apply_changes)
        self.assertTrue(request.register)


if __name__ == "__main__":
    unittest.main()
