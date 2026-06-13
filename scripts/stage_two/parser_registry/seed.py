"""Seed parser registry metadata from JSON configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db import session_scope
from scripts.db.models import ParserRegistry


DEFAULT_SEED_PATH = Path(__file__).with_name("parser_registry_seed.json")


@dataclass(frozen=True)
class ParserRegistrySeedResult:
    """Summary of parser registry seed/update operations."""

    inserted: int
    updated: int


class ParserRegistrySeeder:
    """Seed or update parser_registry rows from a seed JSON file."""

    def __init__(self, session: Session) -> None:
        """Initialize the seeder with an externally managed session."""
        self.session = session

    def seed_from_file(self, seed_path: str | Path = DEFAULT_SEED_PATH) -> ParserRegistrySeedResult:
        """Load parser seed JSON and upsert parser_registry rows."""
        payload = json.loads(Path(seed_path).read_text(encoding="utf-8"))
        return self.seed_payload(payload)

    def seed_payload(self, payload: dict[str, Any]) -> ParserRegistrySeedResult:
        """Upsert parser_registry rows from an already loaded payload."""
        inserted = 0
        updated = 0
        for row in expand_parser_seed(payload):
            existing = self._find_existing(row)
            if existing is None:
                self.session.add(ParserRegistry(**row))
                inserted += 1
            else:
                for key, value in row.items():
                    setattr(existing, key, value)
                updated += 1
        self.session.flush()
        return ParserRegistrySeedResult(inserted=inserted, updated=updated)

    def _find_existing(self, row: dict[str, Any]) -> ParserRegistry | None:
        statement = select(ParserRegistry).where(
            ParserRegistry.parser_name == row["parser_name"],
            ParserRegistry.parser_version == row["parser_version"],
            ParserRegistry.branch == row["branch"],
            ParserRegistry.source_format == row["source_format"],
            ParserRegistry.supported_role.is_(row["supported_role"])
            if row["supported_role"] is None
            else ParserRegistry.supported_role == row["supported_role"],
        )
        return self.session.execute(statement).scalar_one_or_none()


def expand_parser_seed(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand compact parser group seed JSON into parser_registry rows."""
    rows: list[dict[str, Any]] = []
    for group in payload.get("parser_groups", []):
        source_formats = group["source_formats"]
        supported_roles = group.get("supported_roles")
        roles = supported_roles if supported_roles is not None else [None]
        for source_format in source_formats:
            for role in roles:
                row = {
                    "parser_name": group["parser_name"],
                    "parser_version": group["parser_version"],
                    "branch": group["branch"],
                    "source_format": source_format,
                    "supported_role": role,
                    "normalized_schema_name": group["normalized_schema_name"],
                    "normalized_schema_version": group["normalized_schema_version"],
                    "parser_module": group["parser_module"],
                    "parser_class": group["parser_class"],
                    "priority": group.get("priority", 100),
                    "is_active": group.get("is_active", True),
                    "supports_streaming": group.get("supports_streaming", True),
                    "requires_external_tools": group.get("requires_external_tools", False),
                    "external_tools_json": group.get("external_tools_json"),
                    "config_json": group.get("config_json"),
                }
                rows.append(row)
    return rows


def seed_default_parser_registry() -> ParserRegistrySeedResult:
    """Seed the default parser registry in a managed transaction."""
    with session_scope() as session:
        return ParserRegistrySeeder(session).seed_from_file(DEFAULT_SEED_PATH)
