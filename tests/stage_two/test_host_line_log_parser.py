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

    def test_apache_error_line_is_not_treated_as_json_array(self) -> None:
        line = (
            "[Sat Jan 15 06:25:11.555081 2022] [ssl:warn] [pid 29644] "
            "AH01909: 000-catch-all:443:0 server certificate does NOT include an ID which matches the server name"
        )
        path = _write_temp_text(self, line + "\n", file_name="error.log.2")

        result = _parser().parse(path, _context(path, source_format="log-2"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "apache_warn")
        self.assertEqual(event["modality"], "log")
        self.assertEqual(event["process_name"], "apache2")
        self.assertEqual(event["process_id"], "29644")
        self.assertEqual(event["raw_event_name"], "ssl")
        self.assertEqual(event["raw_fields_json"]["message"].startswith("AH01909:"), True)
        self.assertEqual(event["metadata_json"]["apache_module"], "ssl")
        self.assertEqual(event["metadata_json"]["apache_severity"], "warn")

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

    def test_binary_systemd_journal_extracts_message_fields(self) -> None:
        payload = (
            b"LPKSHHRH\x00\x00\x00\x00"
            b"PRIORITY=6\x00"
            b"SYSLOG_IDENTIFIER=systemd\x00"
            b"_PID=1032\x00"
            b"_UID=1000\x00"
            b"_HOSTNAME=aecid-samba-4\x00"
            b"_SOURCE_REALTIME_TIMESTAMP=1642502664000000\x00"
            b"_SYSTEMD_UNIT=user@1000.service\x00"
            b"MESSAGE=Stopped target Default.\x00"
            b"PRIORITY=3\x00"
            b"SYSLOG_IDENTIFIER=kernel\x00"
            b"MESSAGE=Kernel warning emitted.\x00"
        )
        path = _write_temp_bytes(self, payload, file_name="system.journal")

        result = _parser().parse(path, _context(path, source_format="journal"))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual(result.file_status, "PARSED")
        self.assertIn("systemd_journal_binary_fallback=True", result.warnings)
        first = result.events[0]
        self.assertEqual(first["event_type"], "journal_unit")
        self.assertEqual(first["modality"], "journal")
        self.assertEqual(first["host_name"], "aecid-samba-4")
        self.assertEqual(first["process_name"], "systemd")
        self.assertEqual(first["process_id"], "1032")
        self.assertEqual(first["user_name"], "1000")
        self.assertEqual(first["timestamp_type"], "absolute")
        self.assertEqual(first["raw_fields_json"]["message"], "Stopped target Default.")
        self.assertEqual(result.events[1]["event_type"], "journal_error")


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


def _write_temp_bytes(
    test_case: unittest.TestCase,
    content: bytes,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-line-log-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_bytes(content)
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
