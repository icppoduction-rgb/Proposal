"""Seed parser registry metadata from JSON configuration."""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import PARSER_REGISTRY_SEED_PATH
from scripts.db import session_scope
from scripts.db.models import ParserRegistry, SchemaVersion


DEFAULT_SEED_PATH = Path(PARSER_REGISTRY_SEED_PATH)


@dataclass(frozen=True)
class ParserClassValidationResult:
    """Parser class import validation diagnostic."""

    parser_module: str
    parser_class: str
    available: bool
    error: str | None = None
    parser_name: str | None = None
    parser_version: str | None = None
    branch: str | None = None
    source_format: str | None = None
    supported_role: str | None = None

    @property
    def qualified_name(self) -> str:
        """Return module-qualified class name for diagnostics."""
        return f"{self.parser_module}.{self.parser_class}"


@dataclass(frozen=True)
class ParserRegistrySeedResult:
    """Summary of parser registry seed/update operations."""

    inserted: int
    updated: int
    validation_errors: tuple[ParserClassValidationResult, ...] = ()


@dataclass(frozen=True)
class StageTwoMetadataSeedResult:
    """Summary of Stage Two metadata seed/update operations."""

    schema_version_id: int
    schema_name: str
    schema_version: str
    parser_registry: ParserRegistrySeedResult


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
        validation_errors: list[ParserClassValidationResult] = []
        for expanded_row in expand_parser_seed(payload):
            row, validation = prepare_parser_registry_row(expanded_row)
            if expanded_row["is_active"] and not validation.available:
                validation_errors.append(validation)
            existing = self._find_existing(row)
            if existing is None:
                self.session.add(ParserRegistry(**row))
                inserted += 1
            else:
                for key, value in row.items():
                    setattr(existing, key, value)
                updated += 1
        self.session.flush()
        return ParserRegistrySeedResult(
            inserted=inserted,
            updated=updated,
            validation_errors=tuple(validation_errors),
        )

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


def prepare_parser_registry_row(row: Mapping[str, Any]) -> tuple[dict[str, Any], ParserClassValidationResult]:
    """Return a seed row safe for upsert and its class validation result."""
    prepared = dict(row)
    validation = validate_parser_registry_row(prepared)
    if prepared.get("is_active", True) and not validation.available:
        prepared["is_active"] = False
        config_json = dict(prepared.get("config_json") or {})
        config_json["class_validation"] = {
            "status": "inactive_missing_parser_class",
            "parser_module": validation.parser_module,
            "parser_class": validation.parser_class,
            "error": validation.error,
        }
        prepared["config_json"] = config_json
    return prepared, validation


def validate_parser_seed_payload(payload: dict[str, Any]) -> tuple[ParserClassValidationResult, ...]:
    """Validate parser classes referenced by a compact seed payload."""
    return tuple(validate_parser_registry_row(row) for row in expand_parser_seed(payload))


def validate_parser_registry_row(row: Mapping[str, Any] | object) -> ParserClassValidationResult:
    """Validate the parser class referenced by a seed row or ORM object."""
    return validate_parser_class(
        parser_module=str(_field(row, "parser_module")),
        parser_class=str(_field(row, "parser_class")),
        parser_name=_optional_str(_field(row, "parser_name")),
        parser_version=_optional_str(_field(row, "parser_version")),
        branch=_optional_str(_field(row, "branch")),
        source_format=_optional_str(_field(row, "source_format")),
        supported_role=_optional_str(_field(row, "supported_role")),
    )


def validate_parser_class(
    *,
    parser_module: str,
    parser_class: str,
    parser_name: str | None = None,
    parser_version: str | None = None,
    branch: str | None = None,
    source_format: str | None = None,
    supported_role: str | None = None,
) -> ParserClassValidationResult:
    """Return a diagnostic instead of raising when parser import/class lookup fails."""
    try:
        module = importlib.import_module(parser_module)
    except Exception as exc:
        return ParserClassValidationResult(
            parser_module=parser_module,
            parser_class=parser_class,
            available=False,
            error=f"failed to import parser module: {type(exc).__name__}: {exc}",
            parser_name=parser_name,
            parser_version=parser_version,
            branch=branch,
            source_format=source_format,
            supported_role=supported_role,
        )

    parser_type = getattr(module, parser_class, None)
    if parser_type is None:
        return ParserClassValidationResult(
            parser_module=parser_module,
            parser_class=parser_class,
            available=False,
            error="parser class not found in module",
            parser_name=parser_name,
            parser_version=parser_version,
            branch=branch,
            source_format=source_format,
            supported_role=supported_role,
        )

    from scripts.stage_two.parsers.base import BaseParser

    if not isinstance(parser_type, type) or not issubclass(parser_type, BaseParser):
        return ParserClassValidationResult(
            parser_module=parser_module,
            parser_class=parser_class,
            available=False,
            error="parser class is not a BaseParser subclass",
            parser_name=parser_name,
            parser_version=parser_version,
            branch=branch,
            source_format=source_format,
            supported_role=supported_role,
        )

    return ParserClassValidationResult(
        parser_module=parser_module,
        parser_class=parser_class,
        available=True,
        parser_name=parser_name,
        parser_version=parser_version,
        branch=branch,
        source_format=source_format,
        supported_role=supported_role,
    )


def _field(row: Mapping[str, Any] | object, name: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(name)
    return getattr(row, name)


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def seed_default_parser_registry() -> ParserRegistrySeedResult:
    """Seed the default parser registry in a managed transaction."""
    with session_scope() as session:
        return ParserRegistrySeeder(session).seed_from_file(DEFAULT_SEED_PATH)


def seed_stage_two_metadata() -> StageTwoMetadataSeedResult:
    """Seed required Stage Two schema and parser metadata in one transaction."""
    from scripts.stage_two.normalization.schema_contracts import NormalizedSchemaRegistry

    with session_scope() as session:
        schema_version = NormalizedSchemaRegistry(session).register_contract()
        parser_registry = ParserRegistrySeeder(session).seed_from_file(DEFAULT_SEED_PATH)
        return _metadata_seed_result(schema_version, parser_registry)


def _metadata_seed_result(
    schema_version: SchemaVersion,
    parser_registry: ParserRegistrySeedResult,
) -> StageTwoMetadataSeedResult:
    return StageTwoMetadataSeedResult(
        schema_version_id=schema_version.id,
        schema_name=schema_version.schema_name,
        schema_version=schema_version.schema_version,
        parser_registry=parser_registry,
    )
