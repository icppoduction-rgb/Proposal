from __future__ import annotations

import base64
import shutil
import tempfile
import unittest
from pathlib import Path

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
