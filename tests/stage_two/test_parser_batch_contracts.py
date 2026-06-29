from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import REQUIRED_NORMALIZED_FIELDS, ParserContext
from scripts.stage_two.parsers.dns import DnsCsvParser, UnlabeledResolver
from scripts.stage_two.parsers.host import HostJsonLinesParser, HostLineLogParser


class ParserBatchContractTest(unittest.TestCase):
    def test_csv_parser_streams_headered_rows_in_bounded_batches(self) -> None:
        path = _write_temp_text(
            self,
            "query_domain,ttl,custom_col\n"
            "one.example,60,kept-1\n"
            "two.example,61,kept-2\n"
            "three.example,62,kept-3\n",
            file_name="dns.csv",
        )

        batches = list(
            DnsCsvParser(UnlabeledResolver()).parse_batches(
                path,
                _context(path, branch="dns", source_format="csv"),
                batch_size=2,
            )
        )
        non_empty_batches = [batch for batch in batches if batch.events]
        events = [event for batch in non_empty_batches for event in batch.events]

        self.assertEqual([len(batch.events) for batch in non_empty_batches], [2, 1])
        self.assertEqual(sum(batch.rows_read for batch in batches), 3)
        self.assertEqual(sum(batch.rows_parsed for batch in batches), 3)
        self.assertEqual(sum(batch.rows_failed for batch in batches), 0)
        self.assertEqual([event["event_index"] for event in events], [0, 1, 2])
        self.assertEqual(events[0]["raw_fields_json"]["custom_col"], "kept-1")
        self.assertEqual(events[2]["raw_fields_json"]["custom_col"], "kept-3")
        self.assertTrue(REQUIRED_NORMALIZED_FIELDS.issubset(events[0]))

    def test_jsonl_parser_streams_numberlong_without_failing_file(self) -> None:
        lines = [
            '{"@timestamp":"2024-01-01T00:00:00Z","host":{"name":"h1"},'
            '"process":{"pid":NumberLong("123"),"name":"bash"},'
            '"event":{"action":"exec"},"custom":{"nested":"kept"}}',
            json.dumps(
                {
                    "@timestamp": "2024-01-01T00:00:01Z",
                    "host": {"name": "h2"},
                    "process": {"pid": 124, "name": "sshd"},
                    "event": {"action": "login"},
                    "extra": "kept-2",
                }
            ),
            "{bad json}",
        ]
        path = _write_temp_text(self, "\n".join(lines) + "\n", file_name="events.json")

        batches = list(
            HostJsonLinesParser(_label_resolver()).parse_batches(
                path,
                _context(path, branch="host", source_format="json"),
                batch_size=1,
            )
        )
        non_empty_batches = [batch for batch in batches if batch.events]
        events = [event for batch in non_empty_batches for event in batch.events]

        self.assertEqual([len(batch.events) for batch in non_empty_batches], [1, 1])
        self.assertEqual(sum(batch.rows_read for batch in batches), 3)
        self.assertEqual(sum(batch.rows_parsed for batch in batches), 2)
        self.assertEqual(sum(batch.rows_failed for batch in batches), 1)
        self.assertEqual(events[0]["process_id"], "123")
        self.assertEqual(events[0]["raw_fields_json"]["custom.nested"], "kept")
        self.assertEqual(events[1]["raw_fields_json"]["extra"], "kept-2")
        self.assertIn("json line 3", " ".join(error for batch in batches for error in batch.local_errors))
        self.assertTrue(REQUIRED_NORMALIZED_FIELDS.issubset(events[0]))

    def test_log_parser_streams_text_lines_preserving_event_order(self) -> None:
        lines = [
            "Jan 12 08:15:30 web01 sshd[1234]: Accepted password for alice from 10.0.0.5 port 54421 ssh2",
            "Jan 12 08:16:00 web01 su[222]: pam_unix(su:session): session opened for user root by alice(uid=1000)",
            "Jan 12 09:00:00 mail01 postfix/smtpd[2222]: ABC123: client=mx.example[192.0.2.10]",
        ]
        path = _write_temp_text(self, "\n".join(lines) + "\n", file_name="auth.log")

        batches = list(
            HostLineLogParser(_label_resolver()).parse_batches(
                path,
                _context(path, branch="host", source_format="auth.log"),
                batch_size=2,
            )
        )
        non_empty_batches = [batch for batch in batches if batch.events]
        events = [event for batch in non_empty_batches for event in batch.events]

        self.assertEqual([len(batch.events) for batch in non_empty_batches], [2, 1])
        self.assertEqual(sum(batch.rows_read for batch in batches), 3)
        self.assertEqual(sum(batch.rows_parsed for batch in batches), 3)
        self.assertEqual([event["event_index"] for event in events], [0, 1, 2])
        self.assertTrue(all(event["timestamp"] is None for event in events))
        self.assertTrue(all(event["timestamp_type"] == "event_order" for event in events))
        self.assertTrue(all("_raw_line_sha256" in event["raw_fields_json"] for event in events))
        self.assertEqual(events[0]["metadata_json"]["timestamp_parse_status"], "partial_missing_year_timezone")
        self.assertTrue(REQUIRED_NORMALIZED_FIELDS.issubset(events[0]))


def _label_resolver() -> LabelResolver:
    return LabelResolver(config_path=None, enable_filename_heuristics=True)


def _write_temp_text(
    test_case: unittest.TestCase,
    content: str,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="parser-batch-contract-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_text(content, encoding="utf-8")
    return path


def _cleanup_directory(directory: Path) -> None:
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink()
    directory.rmdir()


def _context(
    path: Path,
    *,
    branch: str,
    source_format: str,
    role: str = "TRAIN",
) -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name=f"{branch}-dataset",
        dataset_role=role,
        branch=branch,
        source_format=source_format,
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
    )


if __name__ == "__main__":
    unittest.main()
