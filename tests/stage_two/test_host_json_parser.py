from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.host import HostJsonLinesParser


class HostJsonLinesParserTest(unittest.TestCase):
    def test_json_lines_extracts_ecs_nested_fields(self) -> None:
        rows = [
            {
                "@timestamp": "2024-01-01T00:00:00Z",
                "host": {"name": "host-a"},
                "user": {"name": "alice"},
                "process": {"pid": 123, "name": "bash", "executable": "/bin/bash"},
                "event": {"dataset": "process", "action": "exec"},
                "log": {"file": {"path": "/var/log/filebeat/filebeat"}},
                "message": "process started",
                "rule": {"alert": "alert"},
            },
            {
                "@timestamp": "2024-01-01T00:00:01Z",
                "host": {"name": "host-b"},
                "process": {"pid": 124, "name": "sshd"},
                "event": {"dataset": "auth", "action": "login"},
                "message": "login ok",
            },
        ]
        path = _write_temp_text(self, "\n".join(json.dumps(row) for row in rows) + "\n")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "exec")
        self.assertEqual(event["host_name"], "host-a")
        self.assertEqual(event["user_name"], "alice")
        self.assertEqual(event["process_id"], "123")
        self.assertEqual(event["process_name"], "bash")
        self.assertEqual(event["file_path"], "/bin/bash")
        self.assertEqual(event["raw_fields_json"]["host.name"], "host-a")
        self.assertNotIn("host", event["raw_fields_json"])
        self.assertEqual(event["metadata_json"]["event_dataset"], "process")
        self.assertEqual(event["metadata_json"]["log_file_path"], "/var/log/filebeat/filebeat")
        self.assertEqual(event["label_source"], "ids_alert")

    def test_json_array_extracts_metricbeat_like_record(self) -> None:
        payload = [
            {
                "@timestamp": "2024-01-01T00:00:00Z",
                "host": {"name": "metric-host"},
                "event": {"dataset": "system.cpu", "action": "metric"},
                "metricset": {"name": "cpu"},
                "system": {"cpu": {"total": {"norm": {"pct": 0.5}}}},
            }
        ]
        path = _write_temp_text(self, json.dumps(payload), file_name="events.json-1")

        result = _parser().parse(path, _context(path, source_format="json-1"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["modality"], "metric")
        self.assertEqual(event["metric_name"], "cpu")
        self.assertEqual(event["metric_value"], 0.5)
        self.assertEqual(event["metadata_json"]["json_source_type"], "json_array")

    def test_single_json_object_extracts_sysmon_like_record(self) -> None:
        payload = {
            "@timestamp": "2024-01-01T00:00:00Z",
            "winlog": {
                "event_id": 1,
                "computer_name": "WIN-HOST",
                "event_data": {
                    "Image": r"C:\Windows\System32\cmd.exe",
                    "ProcessId": "4242",
                    "CommandLine": "cmd.exe /c whoami",
                    "User": r"DOMAIN\alice",
                },
            },
            "event": {"provider": "Microsoft-Windows-Sysmon", "action": "Process Create"},
            "message": "Process Create",
        }
        path = _write_temp_text(self, json.dumps(payload), file_name="sysmon.json")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "Process Create")
        self.assertEqual(event["host_name"], "WIN-HOST")
        self.assertEqual(event["process_id"], "4242")
        self.assertEqual(event["process_name"], "cmd.exe")
        self.assertEqual(event["file_path"], r"C:\Windows\System32\cmd.exe")
        self.assertEqual(event["event_id"], "1")
        self.assertEqual(event["command_line"], "cmd.exe /c whoami")
        self.assertEqual(event["metadata_json"]["json_source_type"], "json_object")

    def test_bad_json_line_is_partial_success(self) -> None:
        path = _write_temp_text(
            self,
            json.dumps({"message": "ok-1"}) + "\n"
            "{bad json}\n"
            + json.dumps({"message": "ok-2", "event": {"action": "message"}})
            + "\n",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 3)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual(result.rows_failed, 1)
        self.assertIn("json line 2", result.error_samples[0])

    def test_base64_json_line_is_decoded_by_universal_reader(self) -> None:
        payload = json.dumps(
            {
                "@timestamp": "2024-01-01T00:00:00Z",
                "host": {"name": "encoded-host"},
                "event": {"action": "encoded"},
            }
        )
        encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        path = _write_temp_text(self, encoded + "\n", file_name="encoded.json")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual(result.events[0]["host_name"], "encoded-host")
        self.assertIn("base64_detected=True", result.warnings)


def _parser() -> HostJsonLinesParser:
    return HostJsonLinesParser(LabelResolver(config_path=None, enable_filename_heuristics=True))


def _write_temp_text(
    test_case: unittest.TestCase,
    content: str,
    *,
    file_name: str = "events.json",
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-json-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_text(content, encoding="utf-8")
    return path


def _cleanup_directory(directory: Path) -> None:
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink()
    directory.rmdir()


def _context(path: Path, *, role: str = "TRAIN", source_format: str = "json") -> ParserContext:
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
