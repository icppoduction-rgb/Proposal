from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.dns import DnsCsvParser, UnlabeledResolver


class DnsCsvParserTest(unittest.TestCase):
    def test_train_domain_list_row_without_header(self) -> None:
        path = _write_temp_csv(self, "example.org\n")

        result = DnsCsvParser(UnlabeledResolver()).parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["domain"], "example.org")
        self.assertEqual(event["query_domain"], "example.org")
        self.assertEqual(event["raw_fields_json"]["_csv_schema"], "domain_list")

    def test_test_headerless_22_column_row(self) -> None:
        values = [
            "1704067200",
            "10.0.0.1",
            "8.8.8.8",
            "5353",
            "53",
            "udp",
            "evil.example",
            "A",
            "IN",
            "300",
            "NOERROR",
            "1",
            "12",
            "4",
            "2",
            "1.5",
            "8.8.8.8",
            "example",
            "64500",
            "US",
            "",
            "{}",
        ]
        path = _write_temp_csv(self, ",".join(values) + "\n", file_name="phishing_test.csv")
        parser = DnsCsvParser(LabelResolver(config_path=None, enable_filename_heuristics=True))

        result = parser.parse(path, _context(path, role="TEST"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["src_ip"], "10.0.0.1")
        self.assertEqual(event["dst_ip"], "8.8.8.8")
        self.assertEqual(event["src_port"], 5353)
        self.assertEqual(event["dst_port"], 53)
        self.assertEqual(event["query_domain"], "evil.example")
        self.assertEqual(event["qtype"], "A")
        self.assertEqual(event["ttl"], 300)
        self.assertEqual(event["label_source"], "none")
        self.assertEqual(event["label_status"], "unlabeled")

    def test_phishtank_like_feed_extracts_domain_from_url(self) -> None:
        path = _write_temp_csv(
            self,
            "phish_id,url,phish_detail_url,submission_time,verified\n"
            "1,http://bad.example/path,http://phishtank.test/detail,2024-01-01T00:00:00Z,yes\n"
        )

        result = DnsCsvParser(UnlabeledResolver()).parse(path, _context(path))

        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["query_domain"], "bad.example")
        self.assertEqual(event["timestamp_source"], "submission_time")
        self.assertEqual(event["timestamp_type"], "absolute")
        self.assertEqual(event["raw_fields_json"]["url"], "http://bad.example/path")

    def test_unescaped_list_columns_are_preserved_in_raw_fields(self) -> None:
        path = _write_temp_csv(self, "Domain,TTL,features\ngood.example,60,[\"a\",\"b\"]\n")

        result = DnsCsvParser(UnlabeledResolver()).parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["query_domain"], "good.example")
        self.assertEqual(event["ttl"], 60)
        self.assertEqual(event["raw_fields_json"]["_csv_extra_columns"], ["b]"])
        self.assertEqual(event["metadata_json"]["csv_extra_columns_count"], 1)

    def test_bad_csv_row_increments_failed_counter_without_stopping_file(self) -> None:
        path = _write_temp_csv(self, "Domain,TTL\ngood.example,not-a-ttl\n,not-a-ttl\n")

        result = DnsCsvParser(UnlabeledResolver()).parse(path, _context(path))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 1)
        self.assertEqual(result.events[0]["query_domain"], "good.example")
        self.assertIsNone(result.events[0]["ttl"])
        self.assertEqual(result.events[0]["raw_fields_json"]["TTL"], "not-a-ttl")
        self.assertIn("row has no usable DNS/domain fields", result.error_samples[0])


def _write_temp_csv(test_case: unittest.TestCase, content: str, *, file_name: str = "sample.csv") -> Path:
    directory = Path(tempfile.mkdtemp(prefix="dns-csv-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_text(content, encoding="utf-8")
    return path


def _cleanup_directory(directory: Path) -> None:
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink()
    directory.rmdir()


def _context(path: Path, *, role: str = "TRAIN") -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="dns-dataset",
        dataset_role=role,
        branch="dns",
        source_format="csv",
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
    )


if __name__ == "__main__":
    unittest.main()
