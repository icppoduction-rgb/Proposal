from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.host import HostLineLogParser


class HostLineLogParserTest(unittest.TestCase):
    def test_syslog_line_extracts_prefix_and_auth_success(self) -> None:
        line = "Jan 12 08:15:30 web01 sshd[1234]: Accepted password for alice from 10.0.0.5 port 54421 ssh2"
        path = _write_temp_text(self, line + "\n", file_name="auth.log")

        result = _parser().parse(path, _context(path, source_format="auth.log"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertIsNone(event["timestamp"])
        self.assertEqual(event["timestamp_type"], "event_order")
        self.assertEqual(event["event_index"], 0)
        self.assertEqual(event["event_type"], "auth_login_success")
        self.assertEqual(event["modality"], "auth")
        self.assertEqual(event["host_name"], "web01")
        self.assertEqual(event["process_name"], "sshd")
        self.assertEqual(event["process_id"], "1234")
        self.assertEqual(event["user_name"], "alice")
        self.assertEqual(event["src_ip"], "10.0.0.5")
        self.assertEqual(event["metadata_json"]["partial_timestamp"], "Jan 12 08:15:30")
        self.assertEqual(event["metadata_json"]["timestamp_parse_status"], "partial_missing_year_timezone")
        self.assertIn("_raw_line_sha256", event["raw_fields_json"])

    def test_auth_session_line_extracts_user(self) -> None:
        line = "Jan 12 08:16:00 web01 su[222]: pam_unix(su:session): session opened for user root by alice(uid=1000)"
        path = _write_temp_text(self, line + "\n", file_name="auth.log")

        result = _parser().parse(path, _context(path, source_format="auth.log"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "auth_session_opened")
        self.assertEqual(event["user_name"], "root")
        self.assertEqual(event["process_name"], "su")
        self.assertEqual(event["modality"], "auth")

    def test_json_line_inside_log_uses_json_extraction(self) -> None:
        payload = {
            "@timestamp": "2024-01-01T00:00:00Z",
            "host": {"name": "json-host"},
            "process": {"pid": 321, "name": "python"},
            "event": {"action": "exec", "dataset": "process"},
            "message": "json event",
        }
        path = _write_temp_text(self, json.dumps(payload) + "\n", file_name="mixed.log")

        result = _parser().parse(path, _context(path, source_format="log"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "exec")
        self.assertEqual(event["host_name"], "json-host")
        self.assertEqual(event["process_id"], "321")
        self.assertEqual(event["process_name"], "python")
        self.assertEqual(event["raw_fields_json"]["host.name"], "json-host")
        self.assertIn("_raw_line_sha256", event["raw_fields_json"])
        self.assertEqual(event["metadata_json"]["log_source_type"], "json_line")
        self.assertEqual(event["metadata_json"]["json_source_type"], "log_json_line")

    def test_mail_mainlog_like_line(self) -> None:
        line = "Jan 12 09:00:00 mail01 postfix/smtpd[2222]: ABC123: client=mx.example[192.0.2.10]"
        path = _write_temp_text(self, line + "\n", file_name="mainlog")

        result = _parser().parse(path, _context(path, source_format="mainlog"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "mail_client")
        self.assertEqual(event["modality"], "mail")
        self.assertEqual(event["host_name"], "mail01")
        self.assertEqual(event["process_name"], "postfix/smtpd")
        self.assertEqual(event["process_id"], "2222")
        self.assertEqual(event["src_ip"], "192.0.2.10")
        self.assertEqual(event["metadata_json"]["mail_queue_id"], "ABC123")
        self.assertEqual(event["metadata_json"]["mail_client"], "mx.example")

    def test_bad_line_is_partial_success(self) -> None:
        good = "Jan 12 08:15:30 web01 sshd[1234]: Accepted password for alice from 10.0.0.5 port 54421 ssh2"
        bad = "\x00\x01\x02"
        mail = "Jan 12 09:00:00 mail01 postfix/smtpd[2222]: ABC123: client=mx.example[192.0.2.10]"
        path = _write_temp_text(self, f"{good}\n{bad}\n{mail}\n", file_name="syslog")

        result = _parser().parse(path, _context(path, source_format="syslog"))

        self.assertEqual(result.rows_read, 3)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual(result.rows_failed, 1)
        self.assertIn("invalid control-heavy line", result.error_samples[0])


def _parser() -> HostLineLogParser:
    return HostLineLogParser(LabelResolver(config_path=None, enable_filename_heuristics=True))


def _write_temp_text(
    test_case: unittest.TestCase,
    content: str,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-line-log-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_text(content, encoding="utf-8")
    return path


def _cleanup_directory(directory: Path) -> None:
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink()
    directory.rmdir()


def _context(path: Path, *, role: str = "TRAIN", source_format: str = "auth.log") -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="host-dataset",
        dataset_role=role,
        branch="host",
        source_format=source_format,
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
    )


if __name__ == "__main__":
    unittest.main()
