from __future__ import annotations

import importlib
import json
import unittest
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.stage_two.ingestion.scanner import KNOWN_SOURCE_FORMATS
from scripts.stage_two.parser_registry.seed import expand_parser_seed


SEED_PATH = Path("scripts/stage_two/parser_registry/parser_registry_seed.json")


def _load_seed_payload() -> dict[str, Any]:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


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
        missing_active_classes: list[tuple[str, str, str]] = []
        for row in rows:
            if not row["is_active"]:
                continue
            module = importlib.import_module(row["parser_module"])
            if not hasattr(module, row["parser_class"]):
                missing_active_classes.append(
                    (row["parser_name"], row["parser_module"], row["parser_class"])
                )

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


if __name__ == "__main__":
    unittest.main()
