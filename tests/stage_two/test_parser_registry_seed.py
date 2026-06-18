from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.db.models import ParserRegistry, SchemaVersion
from scripts.stage_two.ingestion.scanner import KNOWN_SOURCE_FORMATS
from scripts.stage_two.parser_registry.resolver import ParserResolver
from scripts.stage_two.parser_registry.seed import (
    expand_parser_seed,
    prepare_parser_registry_row,
    validate_parser_class,
    validate_parser_registry_row,
)
from scripts.stage_two.parsers import DnsCsvParser, PARSER_CLASS_EXPORTS


SEED_PATH = Path("scripts/stage_two/parser_registry/parser_registry_seed.json")


def _load_seed_payload() -> dict[str, Any]:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def _registry_row(
    *,
    parser_name: str,
    parser_class: str,
    priority: int,
) -> ParserRegistry:
    return ParserRegistry(
        parser_name=parser_name,
        parser_version="v1",
        branch="dns",
        source_format="csv",
        supported_role=None,
        normalized_schema_name="normalized_event",
        normalized_schema_version="v1",
        parser_module="scripts.stage_two.parsers.dns",
        parser_class=parser_class,
        priority=priority,
        is_active=True,
        supports_streaming=True,
        requires_external_tools=False,
        external_tools_json=None,
        config_json=None,
    )


class ParserRegistrySeedTest(unittest.TestCase):
    def test_seed_covers_all_known_source_formats(self) -> None:
        rows = expand_parser_seed(_load_seed_payload())
        seeded_formats = {row["source_format"] for row in rows}

        self.assertEqual(set(KNOWN_SOURCE_FORMATS) - seeded_formats, set())

    def test_seed_expands_without_duplicate_unique_keys(self) -> None:
        rows = expand_parser_seed(_load_seed_payload())
        keys = Counter(
            (
                row["parser_name"],
                row["parser_version"],
                row["branch"],
                row["source_format"],
                row["supported_role"],
            )
            for row in rows
        )

        duplicates = [key for key, count in keys.items() if count > 1]
        self.assertEqual(duplicates, [])

    def test_active_parser_classes_exist(self) -> None:
        rows = expand_parser_seed(_load_seed_payload())
        missing_active_classes = [
            validation
            for row in rows
            if row["is_active"]
            for validation in [validate_parser_registry_row(row)]
            if not validation.available
        ]

        self.assertEqual(missing_active_classes, [])

    def test_packet_capture_entries_cover_dns_and_host(self) -> None:
        rows = expand_parser_seed(_load_seed_payload())
        active_packet_entries = {
            (row["branch"], row["source_format"], row["parser_class"])
            for row in rows
            if row["is_active"] and row["source_format"] in {"cap", "pcap", "pcapng"}
        }

        for source_format in ("cap", "pcap", "pcapng"):
            self.assertIn(
                ("dns", source_format, "DnsPacketCaptureParser"),
                active_packet_entries,
            )
            self.assertIn(
                ("host", source_format, "HostPacketCaptureParser"),
                active_packet_entries,
            )

    def test_seed_external_tool_flags_match_in_repo_parsers(self) -> None:
        rows = expand_parser_seed(_load_seed_payload())
        in_repo_parser_classes = {
            "DnsPacketCaptureParser",
            "HostPacketCaptureParser",
            "HostBsonSandboxParser",
        }

        flagged_rows = [
            row
            for row in rows
            if row["parser_class"] in in_repo_parser_classes
            and (row["requires_external_tools"] or row["external_tools_json"] is not None)
        ]

        self.assertEqual(flagged_rows, [])

    def test_validation_helper_reports_missing_parser_class(self) -> None:
        validation = validate_parser_class(
            parser_module="scripts.stage_two.parsers.host",
            parser_class="MissingParserClass",
        )

        self.assertFalse(validation.available)
        self.assertEqual(validation.error, "parser class not found in module")

    def test_prepare_seed_row_deactivates_missing_active_class(self) -> None:
        row = {
            "parser_name": "missing_parser",
            "parser_version": "v1",
            "branch": "host",
            "source_format": "log",
            "supported_role": None,
            "normalized_schema_name": "normalized_event",
            "normalized_schema_version": "v1",
            "parser_module": "scripts.stage_two.parsers.host",
            "parser_class": "MissingParserClass",
            "priority": 1,
            "is_active": True,
            "supports_streaming": True,
            "requires_external_tools": False,
            "external_tools_json": None,
            "config_json": None,
        }

        prepared, validation = prepare_parser_registry_row(row)

        self.assertFalse(validation.available)
        self.assertFalse(prepared["is_active"])
        self.assertEqual(
            prepared["config_json"]["class_validation"]["status"],
            "inactive_missing_parser_class",
        )

    def test_resolver_skips_invalid_active_candidate(self) -> None:
        invalid = _registry_row(
            parser_name="invalid_dns_csv_parser",
            parser_class="MissingParserClass",
            priority=1,
        )
        valid = _registry_row(
            parser_name="dns_csv_parser",
            parser_class="DnsCsvParser",
            priority=10,
        )
        resolver = ParserResolver(session=None)  # type: ignore[arg-type]
        resolver._active_candidates = lambda **_kwargs: [invalid, valid]  # type: ignore[method-assign]

        result = resolver.resolve_with_diagnostics(
            branch="dns",
            role="TRAIN",
            source_format="csv",
        )

        self.assertIs(result.parser, valid)
        self.assertEqual(len(result.diagnostics), 2)
        self.assertFalse(result.diagnostics[0].available)
        self.assertTrue(result.diagnostics[1].available)

    def test_parser_init_exports_current_parser_classes(self) -> None:
        expected_classes = {
            row["parser_class"]
            for row in expand_parser_seed(_load_seed_payload())
            if row["is_active"]
        }

        self.assertEqual(expected_classes - set(PARSER_CLASS_EXPORTS), set())

    def test_resolver_loads_parser_class_from_registry_metadata(self) -> None:
        row = _registry_row(
            parser_name="dns_csv_parser",
            parser_class="DnsCsvParser",
            priority=10,
        )
        resolver = ParserResolver(session=None)  # type: ignore[arg-type]

        parser_class = resolver.load_parser_class(row)

        self.assertIs(parser_class, DnsCsvParser)

    def test_resolver_returns_none_for_unavailable_parser_class(self) -> None:
        row = _registry_row(
            parser_name="missing_dns_csv_parser",
            parser_class="MissingParserClass",
            priority=1,
        )
        resolver = ParserResolver(session=None)  # type: ignore[arg-type]

        parser_class = resolver.load_parser_class(row)

        self.assertIsNone(parser_class)

    def test_resolver_prefers_branch_schema_then_global_schema(self) -> None:
        row = _registry_row(
            parser_name="dns_csv_parser",
            parser_class="DnsCsvParser",
            priority=10,
        )
        branch_schema = SchemaVersion(
            id=7,
            schema_name="normalized_event",
            schema_version="v1",
            layer="normalized",
            branch="dns",
            is_active=True,
        )
        session = _FakeSchemaSession([branch_schema])
        resolver = ParserResolver(session=session)  # type: ignore[arg-type]

        schema = resolver.resolve_schema_version(row, branch="dns")

        self.assertIs(schema, branch_schema)
        self.assertEqual(session.execute_count, 1)

    def test_resolver_falls_back_to_global_schema(self) -> None:
        row = _registry_row(
            parser_name="dns_csv_parser",
            parser_class="DnsCsvParser",
            priority=10,
        )
        global_schema = SchemaVersion(
            id=8,
            schema_name="normalized_event",
            schema_version="v1",
            layer="normalized",
            branch=None,
            is_active=True,
        )
        session = _FakeSchemaSession([None, global_schema])
        resolver = ParserResolver(session=session)  # type: ignore[arg-type]

        schema = resolver.resolve_schema_version(row, branch="dns")

        self.assertIs(schema, global_schema)
        self.assertEqual(session.execute_count, 2)


class _FakeSchemaResult:
    def __init__(self, row: SchemaVersion | None) -> None:
        self.row = row

    def scalar_one_or_none(self) -> SchemaVersion | None:
        return self.row


class _FakeSchemaSession:
    def __init__(self, rows: list[SchemaVersion | None]) -> None:
        self.rows = rows
        self.execute_count = 0

    def execute(self, _statement: object) -> _FakeSchemaResult:
        self.execute_count += 1
        row = self.rows.pop(0) if self.rows else None
        return _FakeSchemaResult(row)


if __name__ == "__main__":
    unittest.main()
