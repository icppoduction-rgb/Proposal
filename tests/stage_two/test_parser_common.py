from __future__ import annotations

import hashlib
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import (
    build_default_label_fields,
    build_normalized_event,
    build_timestamp_fields,
    generate_event_uid,
    merge_json_objects,
)


class _FakeParser(BaseParser):
    parser_name = "fake_parser"

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        return ParserResult(rows_read=0, rows_parsed=0, rows_failed=0, events=[])


class ParserCommonTest(unittest.TestCase):
    def test_generate_event_uid_matches_existing_parser_format(self) -> None:
        context = _context()

        event_uid = generate_event_uid(context, 7, "entity")

        expected = hashlib.sha256(b"/raw/file.csv:7:entity").hexdigest()
        self.assertEqual(event_uid, expected)

    def test_build_normalized_event_defaults_and_overrides(self) -> None:
        context = _context()
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

        event = build_normalized_event(
            context,
            parser_name="fake_parser",
            parser_version="v2",
            schema_name="normalized_event",
            schema_version="v1",
            timestamp=timestamp,
            event_index=3,
            entity_type="domain",
            entity_id="example.org",
            event_type="dns_query",
            modality="dns",
            label_binary=1,
            label_source="embedded_column",
            label_status="explicit_label",
            raw_fields_json={"domain": "example.org"},
        )

        self.assertEqual(event["dataset_id"], 10)
        self.assertEqual(event["file_id"], 20)
        self.assertEqual(event["parser_name"], "fake_parser")
        self.assertEqual(event["parser_version"], "v2")
        self.assertEqual(event["parser_run_id"], 30)
        self.assertEqual(event["timestamp"], timestamp)
        self.assertEqual(event["timestamp_type"], "absolute")
        self.assertEqual(event["event_index"], 3)
        self.assertEqual(event["label_binary"], 1)
        self.assertEqual(event["label_source"], "embedded_column")
        self.assertEqual(event["label_status"], "explicit_label")
        self.assertEqual(event["raw_fields_json"], {"domain": "example.org"})
        self.assertIsNone(event["metadata_json"])

    def test_base_parser_base_event_uses_common_builder_without_field_renames(self) -> None:
        parser = _FakeParser()
        event = parser.base_event(
            _context(),
            event_index=1,
            entity_type="host",
            entity_id="host-a",
            event_type="login",
            modality="auth",
        )

        parser.validate_result(
            ParserResult(rows_read=1, rows_parsed=1, rows_failed=0, events=[event])
        )
        self.assertEqual(event["label_source"], "none")
        self.assertEqual(event["label_status"], "unlabeled")
        self.assertEqual(event["timestamp_type"], "event_order")

    def test_timestamp_and_label_helpers(self) -> None:
        self.assertEqual(
            build_timestamp_fields(event_index=None),
            {
                "timestamp": None,
                "timestamp_source": None,
                "timestamp_type": "missing",
                "event_index": None,
            },
        )
        self.assertEqual(
            build_default_label_fields({"label_status": "weak_label"})["label_status"],
            "weak_label",
        )

    def test_merge_json_objects_compacts_nested_values(self) -> None:
        merged = merge_json_objects(
            {"a": 1, "empty": "", "nested": {"x": None, "y": 2}},
            {"b": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        )

        self.assertEqual(
            merged,
            {
                "a": 1,
                "nested": {"y": 2},
                "b": "2026-01-01T00:00:00+00:00",
            },
        )


def _context() -> ParserContext:
    return ParserContext(
        dataset_id=10,
        file_id=20,
        dataset_name="dataset",
        dataset_role="TRAIN",
        branch="dns",
        source_format="csv",
        source_file_path="/raw/file.csv",
        source_file_hash="hash",
        parser_run_id=30,
    )


if __name__ == "__main__":
    unittest.main()
