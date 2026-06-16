from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.host import HostCsvParser


class HostCsvParserTest(unittest.TestCase):
    def test_adfa_9_column_headered_row(self) -> None:
        path = _write_temp_text(
            self,
            "date,time,process_id,path,sys_call,event_id,attack_cat,attack_subcat,label\n"
            "31/03/2016,2:45:01,1830,/usr/bin/python3.4,142,45354,normal,normal,0\n",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_syscall")
        self.assertEqual(event["timestamp"].year, 2016)
        self.assertEqual(event["timestamp"].day, 31)
        self.assertEqual(event["timestamp_source"], "date+time")
        self.assertEqual(event["process_id"], "1830")
        self.assertEqual(event["file_path"], "/usr/bin/python3.4")
        self.assertEqual(event["syscall_name"], "142")
        self.assertEqual(event["event_id"], "45354")
        self.assertEqual(event["label_binary"], 0)
        self.assertEqual(event["label_source"], "embedded_column")
        self.assertEqual(event["raw_fields_json"]["_csv_schema"], "adfa_9_column")

    def test_adfa_9_column_headerless_row(self) -> None:
        path = _write_temp_text(
            self,
            "31/03/2016,2:45:01,1830,/bin/dbus-daemon,256,45352,exploit,privilege,1\n",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_syscall")
        self.assertEqual(event["process_id"], "1830")
        self.assertEqual(event["file_path"], "/bin/dbus-daemon")
        self.assertEqual(event["label_binary"], 1)
        self.assertEqual(event["raw_fields_json"]["_csv_schema"], "adfa_9_column")

    def test_validation_runs_csv_row(self) -> None:
        path = _write_temp_text(
            self,
            "image_name,scenario_name,is_executing_exploit,warmup_time,recording_time,exploit_start_time\n"
            "ubuntu:20.04,scenario-1,True,30,60,35\n",
            file_name="runs.csv",
        )

        result = _parser().parse(path, _context(path, role="VALIDATION"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_validation_run")
        self.assertEqual(event["modality"], "host_metadata")
        self.assertEqual(event["entity_id"], "scenario-1")
        self.assertEqual(event["label_binary"], 1)
        self.assertEqual(event["label_source"], "scenario_metadata")
        self.assertEqual(event["metadata_json"]["csv_schema"], "validation_runs")
        self.assertEqual(event["metadata_json"]["recording_time"], 60.0)

    def test_feature_description_csv_emits_metadata_event(self) -> None:
        path = _write_temp_text(
            self,
            "Feature No,Feature Name,Type\n1,date,date\n",
            file_name="feature_descr.csv",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_csv_feature_description")
        self.assertEqual(event["modality"], "host_metadata")
        self.assertEqual(event["label_source"], "none")
        self.assertEqual(event["label_status"], "unlabeled")
        self.assertIn("not a host telemetry event", event["metadata_json"]["parser_reason"])
        self.assertIn("csv_schema=feature_description:1", result.warnings)

    def test_test_role_does_not_use_embedded_csv_label(self) -> None:
        path = _write_temp_text(
            self,
            "date,time,process_id,path,sys_call,event_id,attack_cat,attack_subcat,label\n"
            "31/03/2016,2:45:01,1830,/tmp/evil,142,45354,exploit,privilege,1\n",
            file_name="test_labels.csv",
        )

        result = _parser().parse(path, _context(path, role="TEST"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["label_binary"], None)
        self.assertEqual(event["label_source"], "none")
        self.assertEqual(event["label_status"], "unlabeled")

    def test_cp1252_csv_is_read_with_encoding_fallback(self) -> None:
        content = (
            "date,time,process_id,path,sys_call,event_id,attack_cat,attack_subcat,label\n"
            "31/03/2016,2:45:01,1830,/opt/Caf\xe9Tool.exe,142,45354,normal,normal,0\n"
        )
        path = _write_temp_bytes(self, content.encode("cp1252"), file_name="cp1252.csv")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.events[0]["file_path"], "/opt/Caf\xe9Tool.exe")

    def test_utf8_sig_csv_header_is_detected(self) -> None:
        path = _write_temp_text(
            self,
            "date,time,process_id,path,sys_call,event_id,attack_cat,attack_subcat,label\n"
            "31/03/2016,2:45:01,1830,/usr/sbin/cron,142,45354,normal,normal,0\n",
            file_name="utf8sig.csv",
            encoding="utf-8-sig",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.events[0]["file_path"], "/usr/sbin/cron")


def _parser() -> HostCsvParser:
    return HostCsvParser(LabelResolver(config_path=None, enable_filename_heuristics=True))


def _write_temp_text(
    test_case: unittest.TestCase,
    content: str,
    *,
    file_name: str = "sample.csv",
    encoding: str = "utf-8",
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-csv-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_text(content, encoding=encoding)
    return path


def _write_temp_bytes(
    test_case: unittest.TestCase,
    content: bytes,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-csv-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_bytes(content)
    return path


def _cleanup_directory(directory: Path) -> None:
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink()
    directory.rmdir()


def _context(path: Path, *, role: str = "TRAIN") -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="host-dataset",
        dataset_role=role,
        branch="host",
        source_format="csv",
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
    )


if __name__ == "__main__":
    unittest.main()
