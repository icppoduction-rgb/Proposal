from __future__ import annotations

import base64
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.host import HostSyscallTraceParser


class HostSyscallTraceParserTest(unittest.TestCase):
    def test_ghc_like_line_extracts_call_fragments(self) -> None:
        line = 'pid=1337 uid=1000 openat(AT_FDCWD, "/tmp/a", O_RDONLY) = 3'
        path = _write_temp_text(self, line + "\n", file_name="trace.ghc")

        result = _parser().parse(path, _context(path, source_format="ghc"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_index"], 0)
        self.assertEqual(event["timestamp_type"], "event_order")
        self.assertEqual(event["event_type"], "host_syscall")
        self.assertEqual(event["modality"], "syscall")
        self.assertEqual(event["syscall_name"], "openat")
        self.assertEqual(event["process_id"], "1337")
        self.assertEqual(event["user_name"], "1000")
        self.assertEqual(event["metadata_json"]["return_value"], "3")
        self.assertIsNone(event["metadata_json"].get("syscall_id"))
        self.assertEqual(event["raw_fields_json"]["arguments"], 'AT_FDCWD, "/tmp/a", O_RDONLY')

    def test_real_ghc_module_offset_sequence_expands_to_events(self) -> None:
        line = "kernel32.dll+0x14af5 kernel32.dll+0x1d3a ntdll.dll+0x16d33"
        path = _write_temp_text(self, line + "\n", file_name="trace.GHC")

        result = _parser().parse(path, _context(path, source_format="ghc"))

        self.assertEqual(result.rows_read, 3)
        self.assertEqual(result.rows_parsed, 3)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual([event["event_index"] for event in result.events], [0, 1, 2])
        self.assertEqual(result.events[0]["syscall_name"], "kernel32.dll+0x14af5")
        self.assertEqual(result.events[0]["process_name"], "kernel32.dll")
        self.assertEqual(result.events[0]["event_id"], "0x14af5")
        self.assertEqual(result.events[2]["process_name"], "ntdll.dll")
        self.assertEqual(result.events[2]["metadata_json"]["sequence_length"], 3)
        self.assertEqual(result.events[2]["metadata_json"]["token_index"], 2)

    def test_ghc_module_offset_sequence_is_batched_from_single_long_line(self) -> None:
        line = " ".join(f"kernel32.dll+0x{index:x}" for index in range(7))
        path = _write_temp_text(self, line + "\n", file_name="trace.GHC")

        batches = list(_parser().parse_batches(path, _context(path, source_format="ghc"), batch_size=3))

        self.assertEqual([len(batch.events) for batch in batches], [3, 3, 1])
        self.assertEqual(sum(batch.rows_read for batch in batches), 7)
        self.assertEqual(sum(batch.rows_parsed for batch in batches), 7)
        self.assertEqual(sum(batch.rows_failed for batch in batches), 0)
        self.assertEqual(batches[-1].events[-1]["event_index"], 6)
        self.assertEqual(batches[-1].events[-1]["metadata_json"]["sequence_length"], 7)

    def test_sc_like_numeric_syscall_id_line(self) -> None:
        line = "pid=7 syscall=59 args=/bin/sh"
        path = _write_temp_text(self, line + "\n", file_name="trace.sc")

        result = _parser().parse(path, _context(path, source_format="sc"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["syscall_name"], "syscall_59")
        self.assertEqual(event["event_id"], "59")
        self.assertEqual(event["process_id"], "7")
        self.assertEqual(event["raw_fields_json"]["arguments"], "/bin/sh")
        self.assertEqual(event["metadata_json"]["syscall_id"], "59")

    def test_txt_trace_line_extracts_api_process_user_and_path(self) -> None:
        line = r"user=alice process=python api=CreateFileW path=C:\tmp\a.txt args=GENERIC_READ"
        path = _write_temp_text(self, line + "\n", file_name="trace.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["timestamp_type"], "event_order")
        self.assertEqual(event["syscall_name"], "CreateFileW")
        self.assertEqual(event["user_name"], "alice")
        self.assertEqual(event["process_name"], "python")
        self.assertEqual(event["file_path"], r"C:\tmp\a.txt")
        self.assertEqual(event["raw_fields_json"]["arguments"], "GENERIC_READ")

    def test_txt_windows_nt_key_value_trace_line_extracts_method_process_and_time(self) -> None:
        line = (
            r"Time=207628,Pid=788,MethodName=ZwAcceptConnectPort,"
            r"ProcessName=\Device\HarddiskVolume1\WINDOWS\system32\csrss.exe"
        )
        path = _write_temp_text(self, line + "\n", file_name="ZwAcceptConnectPort__da9048cd95.txt")

        result = _parser().parse(path, _context(path, role="TEST", source_format="txt"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_syscall")
        self.assertEqual(event["modality"], "syscall")
        self.assertEqual(event["timestamp_type"], "event_order")
        self.assertEqual(event["syscall_name"], "ZwAcceptConnectPort")
        self.assertEqual(event["process_id"], "788")
        self.assertEqual(event["process_name"], r"\Device\HarddiskVolume1\WINDOWS\system32\csrss.exe")
        self.assertEqual(event["metadata_json"]["relative_timestamp"], "207628")
        self.assertEqual(event["raw_fields_json"]["trace_fields"]["MethodName"], "ZwAcceptConnectPort")

    def test_txt_name_file_emits_sample_metadata_event(self) -> None:
        content = "C:/Documents/gpupdate.exe,pid=660\n"
        path = _write_temp_text(self, content, file_name="name.txt")

        result = _parser().parse(path, _context(path, role="TEST", source_format="txt"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual(result.file_status, "PARSED")
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_sample_metadata")
        self.assertEqual(event["modality"], "host_metadata")
        self.assertEqual(event["process_id"], "660")
        self.assertEqual(event["process_name"], "gpupdate.exe")
        self.assertEqual(event["file_path"], "C:/Documents/gpupdate.exe")
        self.assertEqual(event["metadata_json"]["helper_type"], "host_sample_name")
        self.assertEqual(event["metadata_json"]["helper_action"], "metadata_event_emitted")

    def test_txt_hashed_name_file_emits_sample_metadata_event(self) -> None:
        content = "C:/Documents/VirusShare_0013bad5970be99d0b2c2bfd32675abc.exe,pid=1852\n"
        path = _write_temp_text(self, content, file_name="name__008a1764ec.txt")

        result = _parser().parse(path, _context(path, role="TEST", source_format="txt"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "host_sample_metadata")
        self.assertEqual(event["process_id"], "1852")
        self.assertEqual(event["process_name"], "VirusShare_0013bad5970be99d0b2c2bfd32675abc.exe")
        self.assertTrue(any("helper_type=host_sample_name" in warning for warning in result.warnings))

    def test_txt_sysdig_trace_line_uses_fast_path(self) -> None:
        line = "811 21:13:19.498051939 3 0 apache2 7149 > wait4 res=0"
        path = _write_temp_text(self, line + "\n", file_name="sysdig.txt")

        with patch(
            "scripts.stage_two.parsers.host._host_event_from_row",
            side_effect=AssertionError("sysdig txt fast path should not use generic host row mapping"),
        ):
            result = _parser().parse(path, _context(path, source_format="txt", role="VALIDATION"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["timestamp_type"], "relative")
        self.assertEqual(event["event_type"], "host_syscall")
        self.assertEqual(event["modality"], "syscall")
        self.assertEqual(event["process_name"], "apache2")
        self.assertEqual(event["process_id"], "7149")
        self.assertEqual(event["user_name"], "0")
        self.assertEqual(event["syscall_name"], "wait4")
        self.assertEqual(event["metadata_json"]["trace_source_type"], "sysdig_trace")
        self.assertEqual(event["metadata_json"]["relative_timestamp"], "21:13:19.498051939")
        self.assertEqual(event["metadata_json"]["return_value"], "0")

    def test_txt_numeric_syscall_sequence_expands_without_base64_decode(self) -> None:
        path = _write_temp_text(self, "168 265 3 168\n", file_name="adfa-sequence.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 4)
        self.assertEqual(result.rows_parsed, 4)
        self.assertEqual(result.rows_failed, 0)
        self.assertNotIn("base64_detected=True", result.warnings)
        self.assertEqual([event["syscall_name"] for event in result.events], ["syscall_168", "syscall_265", "syscall_3", "syscall_168"])
        self.assertEqual(result.events[1]["event_id"], "265")
        self.assertEqual(result.events[1]["metadata_json"]["sequence_length"], 4)
        self.assertEqual(result.events[1]["metadata_json"]["token_index"], 1)

    def test_txt_alert_csv_delegates_to_host_csv_parser(self) -> None:
        content = (
            "time,name,ip,host,short,time_label,event_label\n"
            "1643932807,Suricata: Alert - ET INFO Observed DNS Query,192.168.131.109,internal_share,S-Dns-Qry3,false_positive,dnsteal\n"
        )
        path = _write_temp_text(self, content, file_name="alerts.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "S-Dns-Qry3")
        self.assertEqual(event["raw_event_name"], "Suricata: Alert - ET INFO Observed DNS Query")
        self.assertEqual(event["host_name"], "internal_share")
        self.assertEqual(event["src_ip"], "192.168.131.109")
        self.assertEqual(event["timestamp_type"], "absolute")
        self.assertEqual(event["metadata_json"]["csv_schema"], "host_csv")

    def test_base64_line_is_decoded_safely(self) -> None:
        decoded = "pid=9 uid=1000 close(3) = 0"
        encoded = base64.b64encode(decoded.encode("utf-8")).decode("ascii")
        path = _write_temp_text(self, encoded + "\n", file_name="trace.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["syscall_name"], "close")
        self.assertEqual(event["process_id"], "9")
        self.assertEqual(event["metadata_json"]["return_value"], "0")
        self.assertIn("base64_detected=True", result.warnings)

    def test_readme_like_txt_is_skipped_with_parser_report(self) -> None:
        path = _write_temp_text(self, "# README\nThis dataset contains traces.\n", file_name="README.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 0)
        self.assertEqual(result.rows_parsed, 0)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual(result.file_status, "SKIPPED")
        self.assertTrue(any("parser_report_status=SKIPPED" in warning for warning in result.warnings))

    def test_syscall_reference_txt_is_skipped_with_parser_report(self) -> None:
        content = (
            "#if !defined(_ASM_GENERIC_UNISTD_H) || defined(__SYSCALL)\n"
            "#define __NR_io_setup 0\n"
            "__SYSCALL(__NR_io_setup, sys_io_setup)\n"
        )
        path = _write_temp_text(self, content, file_name="ADFA-LD+Syscall+List.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 0)
        self.assertEqual(result.rows_parsed, 0)
        self.assertEqual(result.rows_failed, 0)
        self.assertEqual(result.file_status, "SKIPPED")
        self.assertTrue(any("helper_type=syscall_reference" in warning for warning in result.warnings))

    def test_empty_trace_file_returns_empty_file_status(self) -> None:
        path = _write_temp_text(self, "", file_name="empty.txt")

        result = _parser().parse(path, _context(path, source_format="txt"))

        self.assertEqual(result.rows_read, 0)
        self.assertEqual(result.rows_parsed, 0)
        self.assertEqual(result.file_status, "EMPTY_FILE")

    def test_bad_line_is_partial_success(self) -> None:
        content = "openat(/tmp/a) = 3\n\x00\x01\x02\nclose(3) = 0\n"
        path = _write_temp_text(self, content, file_name="trace.sc")

        result = _parser().parse(path, _context(path, source_format="sc"))

        self.assertEqual(result.rows_read, 3)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual(result.rows_failed, 1)
        self.assertIn("invalid control-heavy trace line", result.error_samples[0])


def _parser() -> HostSyscallTraceParser:
    return HostSyscallTraceParser(LabelResolver(config_path=None, enable_filename_heuristics=False))


def _write_temp_text(
    test_case: unittest.TestCase,
    content: str,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-syscall-trace-parser-"))
    test_case.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    path = directory / file_name
    path.write_text(content, encoding="utf-8")
    return path


def _context(path: Path, *, role: str = "TRAIN", source_format: str = "txt") -> ParserContext:
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
