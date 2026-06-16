from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import LabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.host import HostXmlParser


class HostXmlParserTest(unittest.TestCase):
    def test_simple_event_xml(self) -> None:
        path = _write_temp_text(
            self,
            """<?xml version="1.0" encoding="utf-8"?>
<Events>
  <Event>
    <Timestamp>2024-01-01T00:00:00Z</Timestamp>
    <Host>host-a</Host>
    <ProcessName>sshd</ProcessName>
    <EventID>1001</EventID>
    <UserName>alice</UserName>
    <Message>login accepted</Message>
  </Event>
</Events>
""",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        self.assertEqual(result.rows_failed, 0)
        event = result.events[0]
        self.assertEqual(event["timestamp_type"], "absolute")
        self.assertEqual(event["host_name"], "host-a")
        self.assertEqual(event["process_name"], "sshd")
        self.assertEqual(event["event_id"], "1001")
        self.assertEqual(event["user_name"], "alice")
        self.assertEqual(event["message"], "login accepted")
        self.assertEqual(event["event_type"], "host_xml_event_1001")
        self.assertEqual(event["raw_fields_json"]["Message"], "login accepted")

    def test_nested_windows_event_xml(self) -> None:
        path = _write_temp_text(
            self,
            """<Event>
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing" />
    <EventID>4624</EventID>
    <TimeCreated SystemTime="2024-01-01T00:00:01Z" />
    <Computer>host01</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserName">alice</Data>
    <Data Name="ProcessName">lsass.exe</Data>
    <Data Name="Message">An account was successfully logged on.</Data>
  </EventData>
</Event>
""",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["timestamp_type"], "absolute")
        self.assertEqual(event["event_type"], "windows_event_4624")
        self.assertEqual(event["modality"], "host_eventlog")
        self.assertEqual(event["host_name"], "host01")
        self.assertEqual(event["user_name"], "alice")
        self.assertEqual(event["process_name"], "lsass.exe")
        self.assertEqual(event["metadata_json"]["provider"], "Microsoft-Windows-Security-Auditing")
        self.assertEqual(event["raw_fields_json"]["EventData.SubjectUserName"], "alice")

    def test_xxe_like_content_is_rejected_safely(self) -> None:
        path = _write_temp_text(
            self,
            """<?xml version="1.0"?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<Event><Message>&xxe;</Message></Event>
""",
        )

        result = _parser().parse(path, _context(path))

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 0)
        self.assertEqual(result.rows_failed, 1)
        self.assertIn("unsafe_xml_rejected=True", result.warnings)
        self.assertIn("unsafe XML DTD/entity declaration rejected", result.error_samples[0])


def _parser() -> HostXmlParser:
    return HostXmlParser(LabelResolver(config_path=None, enable_filename_heuristics=False))


def _write_temp_text(test_case: unittest.TestCase, content: str) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="host-xml-parser-"))
    test_case.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    path = directory / "events.xml"
    path.write_text(content, encoding="utf-8")
    return path


def _context(path: Path, *, role: str = "TRAIN") -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name="host-dataset",
        dataset_role=role,
        branch="host",
        source_format="xml",
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
        metadata={"scenario_name": "xml-smoke"},
    )


if __name__ == "__main__":
    unittest.main()
