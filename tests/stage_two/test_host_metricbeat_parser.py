from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.host import HostLineLogParser
from scripts.stage_two.parsers.metrics import HostMetricbeatParser


class HostMetricbeatParserTest(unittest.TestCase):
    def test_cpu_log_extracts_metricbeat_values(self) -> None:
        row = {
            "@timestamp": "2024-01-01T00:00:00Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.cpu"},
            "metricset": {"module": "system", "name": "cpu"},
            "system": {
                "cpu": {
                    "total": {"norm": {"pct": 0.42}},
                    "user": {"pct": 0.10},
                }
            },
        }
        path = _write_json_lines(self, [row], file_name="cpu.log")

        result = _metric_parser().parse(path, _context(path, source_format="cpu.log"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_failed, 0)
        self.assertGreaterEqual(result.rows_parsed, 2)
        metric = _event_by_metric(result.events, "system.cpu.total.norm.pct")
        self.assertEqual(metric["timestamp_type"], "absolute")
        self.assertEqual(metric["host_name"], "host-a")
        self.assertEqual(metric["event_dataset"], "system.cpu")
        self.assertEqual(metric["metric_value"], 0.42)
        self.assertEqual(metric["modality"], "host_metric")
        self.assertEqual(metric["raw_fields_json"]["system.cpu.total.norm.pct"], 0.42)

    def test_diskio_log_extracts_device_counters(self) -> None:
        row = {
            "@timestamp": "2024-01-01T00:00:01Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.diskio"},
            "metricset": {"module": "system", "name": "diskio"},
            "system": {
                "diskio": {
                    "name": "sda",
                    "read": {"bytes": 1024},
                    "write": {"bytes": 2048},
                }
            },
        }
        path = _write_json_lines(self, [row], file_name="diskio.log")

        result = _metric_parser().parse(path, _context(path, source_format="diskio.log"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_failed, 0)
        self.assertIn("system.diskio.read.bytes", {event["metric_name"] for event in result.events})
        read_metric = _event_by_metric(result.events, "system.diskio.read.bytes")
        self.assertEqual(read_metric["metric_value"], 1024.0)
        self.assertEqual(read_metric["metadata_json"]["disk_name"], "sda")

    def test_network_and_process_summary_logs_extract_metrics(self) -> None:
        network_row = {
            "@timestamp": "2024-01-01T00:00:02Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.network"},
            "system": {
                "network": {
                    "name": "eth0",
                    "in": {"bytes": 4096},
                    "out": {"packets": 16},
                }
            },
        }
        process_summary_row = {
            "@timestamp": "2024-01-01T00:00:03Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.process.summary"},
            "system": {
                "process": {
                    "summary": {
                        "running": 2,
                        "sleeping": 30,
                        "total": 40,
                    }
                }
            },
        }
        network_path = _write_json_lines(self, [network_row], file_name="network.log")
        summary_path = _write_json_lines(self, [process_summary_row], file_name="process.summary.log")

        network_result = _metric_parser().parse(network_path, _context(network_path, source_format="network.log"))
        summary_result = _metric_parser().parse(
            summary_path,
            _context(summary_path, source_format="process.summary.log"),
        )

        network_metric = _event_by_metric(network_result.events, "system.network.in.bytes")
        summary_metric = _event_by_metric(summary_result.events, "system.process.summary.running")
        self.assertEqual(network_metric["network_interface"], "eth0")
        self.assertEqual(network_metric["metric_value"], 4096.0)
        self.assertEqual(summary_metric["metric_value"], 2.0)
        self.assertEqual(summary_metric["event_dataset"], "system.process.summary")

    def test_annotation_rows_do_not_corrupt_metric_rows(self) -> None:
        annotation = {"label": "attack", "annotation": "operator note"}
        metric = {
            "@timestamp": "2024-01-01T00:00:04Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.cpu"},
            "system": {"cpu": {"total": {"norm": {"pct": 0.5}}}},
        }
        path = _write_json_lines(self, [annotation, metric], file_name="cpu.log")

        result = _metric_parser().parse(path, _context(path, source_format="cpu.log"))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual(len([event for event in result.events if event["metric_name"] == "system.cpu.total.norm.pct"]), 1)
        self.assertIn("annotation_rows_skipped=1", result.warnings)
        self.assertTrue(all(event["label_status"] == "unlabeled" for event in result.events))

    def test_missing_service_metric_value_is_null(self) -> None:
        row = {
            "@timestamp": "2024-01-01T00:00:05Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.service"},
            "system": {"service": {"name": "sshd", "state": "running"}},
        }
        path = _write_json_lines(self, [row], file_name="service.log")

        result = _metric_parser().parse(path, _context(path, source_format="service.log"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["metric_name"], "system.service")
        self.assertIsNone(event["metric_value"])
        self.assertEqual(event["service_name"], "sshd")
        self.assertEqual(event["service_state"], "running")

    def test_line_log_parser_delegates_metric_source_formats(self) -> None:
        row = {
            "@timestamp": "2024-01-01T00:00:06Z",
            "host": {"name": "host-a"},
            "event": {"dataset": "system.memory"},
            "system": {"memory": {"actual": {"used": {"pct": 0.7}}}},
        }
        path = _write_json_lines(self, [row], file_name="memory.log")

        result = _line_log_parser().parse(path, _context(path, source_format="memory.log"))

        metric = _event_by_metric(result.events, "system.memory.actual.used.pct")
        self.assertEqual(metric["modality"], "host_metric")
        self.assertEqual(metric["metric_value"], 0.7)


def _metric_parser() -> HostMetricbeatParser:
    return HostMetricbeatParser(LabelResolver(config_path=None, enable_filename_heuristics=False))


def _line_log_parser() -> HostLineLogParser:
    return HostLineLogParser(LabelResolver(config_path=None, enable_filename_heuristics=False))


def _write_json_lines(
    test_case: unittest.TestCase,
    rows: list[dict[str, Any]],
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-metricbeat-parser-"))
    test_case.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    path = directory / file_name
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def _context(path: Path, *, role: str = "TRAIN", source_format: str = "cpu.log") -> ParserContext:
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


def _event_by_metric(events: list[dict[str, Any]], metric_name: str) -> dict[str, Any]:
    for event in events:
        if event["metric_name"] == metric_name:
            return event
    raise AssertionError(f"metric event not found: {metric_name}")


if __name__ == "__main__":
    unittest.main()
