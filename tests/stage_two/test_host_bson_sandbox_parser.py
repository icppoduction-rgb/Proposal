from __future__ import annotations

import base64
import shutil
import struct
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.bson import HostBsonSandboxParser


class HostBsonSandboxParserTest(unittest.TestCase):
    def test_descriptor_and_event_bson_stream_maps_arguments(self) -> None:
        stream = _bson_stream(
            {
                "I": 1001,
                "name": "CreateFileW",
                "type": "api",
                "category": "file",
                "args": [{"name": "path"}, {"name": "desired_access"}],
            },
            {
                "I": 1001,
                "T": 44,
                "t": 12.5,
                "h": 7,
                "pid": 1337,
                "process_name": "sample.exe",
                "args": [r"C:\tmp\a.dll", "GENERIC_READ"],
            },
        )
        path = _write_bytes(self, stream, file_name="sample.bson")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        self.assertIn("descriptor_documents=1", result.warnings)
        event = result.events[0]
        self.assertEqual(event["event_index"], 0)
        self.assertEqual(event["timestamp_type"], "relative")
        self.assertEqual(event["event_type"], "CreateFileW")
        self.assertEqual(event["syscall_name"], "CreateFileW")
        self.assertEqual(event["event_id"], "7")
        self.assertEqual(event["process_id"], "1337")
        self.assertEqual(event["process_name"], "sample.exe")
        self.assertEqual(event["file_path"], r"C:\tmp\a.dll")
        self.assertEqual(event["metadata_json"]["descriptor_id"], "1001")
        self.assertEqual(event["metadata_json"]["category"], "file")
        self.assertEqual(event["metadata_json"]["thread_id"], 44)
        self.assertEqual(event["metadata_json"]["relative_time"], 12.5)
        self.assertEqual(event["raw_fields_json"]["mapped_arguments"]["path"], r"C:\tmp\a.dll")
        self.assertEqual(event["raw_fields_json"]["mapped_arguments"]["desired_access"], "GENERIC_READ")

    def test_relative_timestamp_and_event_index_order_are_preserved(self) -> None:
        stream = _bson_stream(
            {"I": 2001, "name": "RegOpenKeyExW", "type": "api", "category": "registry", "args": ["key"]},
            {"I": 2001, "T": 1, "t": 1.0, "args": [r"HKCU\Software"]},
            {"I": 2001, "T": 1, "t": 2.0, "args": [r"HKLM\Software"]},
        )
        path = _write_bytes(self, stream, file_name="ordered.bson")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 3)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual([event["event_index"] for event in result.events], [0, 1])
        self.assertEqual([event["metadata_json"]["relative_time"] for event in result.events], [1.0, 2.0])
        self.assertTrue(all(event["timestamp_type"] == "relative" for event in result.events))

    def test_unknown_bson_type_is_document_level_failure(self) -> None:
        stream = _unknown_type_document() + _bson_stream({"api": "CloseHandle", "pid": 5, "args": [123]})
        path = _write_bytes(self, stream, file_name="unknown-type.bson")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 1)
        self.assertIn("unsupported BSON element type", result.error_samples[0])
        self.assertEqual(result.events[0]["event_type"], "CloseHandle")

    def test_base64_wrapped_bson_stream_is_decoded_to_bytes(self) -> None:
        stream = _bson_stream(
            {"I": 3001, "name": "ProcessCreate", "type": "api", "category": "process", "args": ["command_line"]},
            {"I": 3001, "t": 3.0, "args": ["cmd.exe /c whoami"]},
        )
        encoded = base64.b64encode(stream)
        path = _write_bytes(self, encoded, file_name="wrapped.bson")

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["event_type"], "ProcessCreate")
        self.assertEqual(event["command_line"], "cmd.exe /c whoami")
        self.assertIn("base64_detected=True", result.warnings)


def _parser() -> HostBsonSandboxParser:
    return HostBsonSandboxParser(LabelResolver(config_path=None, enable_filename_heuristics=False))


def _context(path: Path, *, role: str = "TEST") -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="host-dataset",
        dataset_role=role,
        branch="host",
        source_format="bson",
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
    )


def _write_bytes(
    test_case: unittest.TestCase,
    content: bytes,
    *,
    file_name: str,
) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-bson-parser-"))
    test_case.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    path = directory / file_name
    path.write_bytes(content)
    return path


def _bson_stream(*documents: dict[str, Any]) -> bytes:
    return b"".join(_encode_document(document) for document in documents)


def _encode_document(document: dict[str, Any]) -> bytes:
    body = b"".join(_encode_element(key, value) for key, value in document.items()) + b"\x00"
    return struct.pack("<i", len(body) + 4) + body


def _encode_element(key: str, value: Any) -> bytes:
    key_bytes = key.encode("utf-8") + b"\x00"
    if value is None:
        return b"\x0A" + key_bytes
    if isinstance(value, bool):
        return b"\x08" + key_bytes + (b"\x01" if value else b"\x00")
    if isinstance(value, int):
        if -(2**31) <= value < 2**31:
            return b"\x10" + key_bytes + struct.pack("<i", value)
        return b"\x12" + key_bytes + struct.pack("<q", value)
    if isinstance(value, float):
        return b"\x01" + key_bytes + struct.pack("<d", value)
    if isinstance(value, str):
        encoded = value.encode("utf-8") + b"\x00"
        return b"\x02" + key_bytes + struct.pack("<i", len(encoded)) + encoded
    if isinstance(value, datetime):
        milliseconds = int(value.astimezone(timezone.utc).timestamp() * 1000)
        return b"\x09" + key_bytes + struct.pack("<q", milliseconds)
    if isinstance(value, dict):
        return b"\x03" + key_bytes + _encode_document(value)
    if isinstance(value, list):
        return b"\x04" + key_bytes + _encode_document({str(index): item for index, item in enumerate(value)})
    if isinstance(value, bytes):
        return b"\x05" + key_bytes + struct.pack("<i", len(value)) + b"\x00" + value
    raise TypeError(f"unsupported BSON test value: {value!r}")


def _unknown_type_document() -> bytes:
    body = b"\x2A" + b"x\x00" + b"\x00"
    return struct.pack("<i", len(body) + 4) + body


if __name__ == "__main__":
    unittest.main()
