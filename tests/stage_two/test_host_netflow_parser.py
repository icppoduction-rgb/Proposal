from __future__ import annotations

import base64
import gzip
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parser_registry.seed import expand_parser_seed, validate_parser_registry_row
from scripts.stage_two.parsers.base import REQUIRED_NORMALIZED_FIELDS, ParserContext
from scripts.stage_two.parsers.host import HostNetflowParser


SEED_PATH = Path("scripts/stage_two/parser_registry/parser_registry_seed.json")


class HostNetflowParserTest(unittest.TestCase):
    def test_netflow_day_headerless_11_column_row(self) -> None:
        path = _write_temp_text(
            self,
            "1,2,Comp1,Comp2,6,Port12345,Port80,10,20,1000,2000\n",
            file_name="netflow_day",
        )

        result = _parser().parse(path, _context(path, source_format="netflow_day"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["modality"], "network_flow")
        self.assertEqual(event["event_type"], "network_flow")
        self.assertEqual(event["timestamp_type"], "relative")
        self.assertEqual(event["src_ip"], "Comp1")
        self.assertEqual(event["dst_ip"], "Comp2")
        self.assertEqual(event["protocol"], "TCP")
        self.assertEqual(event["src_port"], 12345)
        self.assertEqual(event["dst_port"], 80)
        self.assertEqual(event["features_json"]["bytes"], 3000.0)
        self.assertEqual(event["features_json"]["packets"], 30.0)
        self.assertEqual(event["features_json"]["duration"], 2.0)
        self.assertEqual(event["metadata_json"]["netflow_schema"], "netflow_day_11_column")
        self.assertTrue(REQUIRED_NORMALIZED_FIELDS.issubset(event))
        self.assertEqual(event["label_status"], "unlabeled")
        self.assertNotIn("_raw_line_sha256", event["raw_fields_json"])
        self.assertNotIn("raw_line_sha256", event["metadata_json"])

    def test_netflow_day_headerless_uses_fast_path_without_generic_pick(self) -> None:
        path = _write_temp_text(
            self,
            "1,2,Comp1,Comp2,6,Port12345,Port80,10,20,1000,2000\n",
            file_name="netflow_day",
        )

        with patch(
            "scripts.stage_two.parsers.netflow._pick",
            side_effect=AssertionError("netflow_day fast path should not use generic _pick"),
        ):
            result = _parser().parse(path, _context(path, source_format="netflow_day"))

        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.events[0]["features_json"]["bytes"], 3000.0)

    def test_headered_whitespace_flow_record(self) -> None:
        path = _write_temp_text(
            self,
            "timestamp src_ip dst_ip src_port dst_port protocol bytes packets duration direction\n"
            "2024-01-01T00:00:00Z 10.0.0.1 10.0.0.2 12345 443 tcp 100 3 0.5 outbound\n",
            file_name="netflow_ids",
        )

        result = _parser().parse(path, _context(path, source_format="netflow_ids"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertIn("header_rows_skipped=1", result.warnings)
        event = result.events[0]
        self.assertEqual(event["timestamp_type"], "absolute")
        self.assertEqual(event["modality"], "host_network_flow")
        self.assertEqual(event["src_ip"], "10.0.0.1")
        self.assertEqual(event["dst_ip"], "10.0.0.2")
        self.assertEqual(event["features_json"]["direction"], "outbound")

    def test_netflow_ids_json_line_alert(self) -> None:
        row = {
            "timestamp": "2024-01-01T00:00:01Z",
            "event_type": "alert",
            "src_ip": "10.0.0.10",
            "src_port": 51515,
            "dest_ip": "10.0.0.20",
            "dest_port": 80,
            "proto": "TCP",
            "flow_id": 123,
            "flow": {
                "bytes_toserver": 100,
                "bytes_toclient": 200,
                "pkts_toserver": 2,
                "pkts_toclient": 3,
            },
            "alert": {
                "category": "Attempted Administrator Privilege Gain",
                "signature": "Test IDS alert",
                "severity": 1,
            },
        }
        path = _write_json_lines(self, [row], file_name="eve.json")

        result = _parser().parse(path, _context(path, source_format="netflow_ids", role="VALIDATION"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "ids_alert")
        self.assertEqual(event["modality"], "host_network_flow")
        self.assertEqual(event["src_ip"], "10.0.0.10")
        self.assertEqual(event["dst_ip"], "10.0.0.20")
        self.assertEqual(event["features_json"]["bytes"], 300.0)
        self.assertEqual(event["features_json"]["packets"], 5.0)
        self.assertEqual(event["metadata_json"]["alert_category"], "Attempted Administrator Privilege Gain")
        self.assertEqual(event["metadata_json"]["alert_signature"], "Test IDS alert")

    def test_wls_day_json_line_eventlog(self) -> None:
        row = {
            "EventID": 4624,
            "UserName": "alice",
            "LogHost": "host01",
            "Source": "Microsoft-Windows-Security-Auditing",
            "Time": 42,
            "DomainName": "EXAMPLE",
            "LogonID": "0x123",
            "ProcessName": "lsass.exe",
        }
        path = _write_json_lines(self, [row], file_name="wls_day")

        result = _parser().parse(path, _context(path, source_format="wls_day", role="VALIDATION"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["modality"], "host_eventlog")
        self.assertEqual(event["event_type"], "windows_event_4624")
        self.assertEqual(event["event_id"], "4624")
        self.assertEqual(event["host_name"], "host01")
        self.assertEqual(event["user_name"], "alice")
        self.assertEqual(event["timestamp_type"], "relative")
        self.assertEqual(event["metadata_json"]["relative_time"], 42.0)
        self.assertEqual(event["metadata_json"]["logon_id"], "0x123")

    def test_wls_day_json_line_uses_fast_path_without_generic_pick(self) -> None:
        row = {
            "EventID": 4688,
            "UserName": "alice",
            "LogHost": "host01",
            "DomainName": "EXAMPLE",
            "ParentProcessName": "services",
            "ParentProcessID": "0x2ac",
            "ProcessName": "svchost.exe",
            "Time": 1,
        }
        path = _write_json_lines(self, [row], file_name="wls_day")

        with patch(
            "scripts.stage_two.parsers.netflow._pick",
            side_effect=AssertionError("wls_day fast path should not use generic _pick"),
        ):
            result = _parser().parse(path, _context(path, source_format="wls_day", role="VALIDATION"))

        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "windows_event_4688")
        self.assertEqual(event["process_name"], "svchost.exe")
        self.assertEqual(event["parent_process_id"], "0x2ac")
        self.assertEqual(event["metadata_json"]["record_source_type"], "json_line_fast")
        self.assertNotIn("_line_number", event["raw_fields_json"])

    def test_wls_day_batches_keep_global_event_order(self) -> None:
        rows = [
            {"EventID": 4624, "UserName": "alice", "LogHost": "host01", "Time": 1},
            {"EventID": 4672, "UserName": "alice", "LogHost": "host01", "Time": 2},
            {"EventID": 4688, "UserName": "alice", "LogHost": "host01", "Time": 3},
        ]
        path = _write_json_lines(self, rows, file_name="wls_day")

        batches = list(
            _parser().parse_batches(
                path,
                _context(path, source_format="wls_day", role="VALIDATION"),
                batch_size=2,
            )
        )
        events = [event for batch in batches for event in batch.events]

        self.assertEqual([len(batch.events) for batch in batches if batch.events], [2, 1])
        self.assertEqual([event["event_index"] for event in events], [0, 1, 2])
        self.assertEqual(len({event["event_uid"] for event in events}), 3)

    def test_base64_wrapped_netflow_text(self) -> None:
        content = "1,2,Comp1,Comp2,17,Port53,Port53000,1,2,64,128\n"
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        path = _write_temp_text(self, encoded, file_name="netflow_day.b64")

        result = _parser().parse(path, _context(path, source_format="netflow_day"))

        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.events[0]["protocol"], "UDP")
        self.assertIn("base64_detected=True", result.warnings)

    def test_gzip_wrapped_netflow_text(self) -> None:
        content = "1,2,Comp1,Comp2,6,Port12345,Port443,1,2,64,128\n"
        path = _write_temp_bytes(self, gzip.compress(content.encode("utf-8")), file_name="netflow_day.gz")

        result = _parser().parse(path, _context(path, source_format="netflow_day"))

        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.events[0]["dst_port"], 443)

    def test_registry_seed_activates_netflow_formats(self) -> None:
        rows = expand_parser_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
        active_rows = {
            row["source_format"]: row
            for row in rows
            if row["branch"] == "host" and row["source_format"] in {"netflow_day", "netflow_ids", "wls_day"}
        }

        self.assertEqual(set(active_rows), {"netflow_day", "netflow_ids", "wls_day"})
        for row in active_rows.values():
            self.assertTrue(row["is_active"])
            self.assertEqual(row["parser_class"], "HostNetflowParser")
            self.assertTrue(validate_parser_registry_row(row).available)


def _parser() -> HostNetflowParser:
    return HostNetflowParser(LabelResolver(config_path=None, enable_filename_heuristics=False))


def _write_temp_text(
    test_case: unittest.TestCase,
    content: str,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-netflow-parser-"))
    test_case.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    path = directory / file_name
    path.write_text(content, encoding="utf-8")
    return path


def _write_temp_bytes(
    test_case: unittest.TestCase,
    content: bytes,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-netflow-parser-"))
    test_case.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    path = directory / file_name
    path.write_bytes(content)
    return path


def _write_json_lines(
    test_case: unittest.TestCase,
    rows: list[dict[str, Any]],
    *,
    file_name: str,
) -> Path:
    content = "\n".join(json.dumps(row) for row in rows) + "\n"
    return _write_temp_text(test_case, content, file_name=file_name)


def _context(path: Path, *, role: str = "TRAIN", source_format: str = "netflow_day") -> ParserContext:
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
        metadata={"scenario_name": "scenario-a"},
    )


if __name__ == "__main__":
    unittest.main()
