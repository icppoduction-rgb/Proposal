from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.db.models import ParserRegistry
from scripts.stage_two.ingestion.scanner import KNOWN_SOURCE_FORMATS
from scripts.stage_two.parser_registry.resolver import ParserResolver
from scripts.stage_two.parser_registry.seed import (
    expand_parser_seed,
    prepare_parser_registry_row,
    validate_parser_class,
    validate_parser_registry_row,
)
from scripts.stage_two.parsers import PARSER_CLASS_EXPORTS


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


if __name__ == "__main__":
    unittest.main()
