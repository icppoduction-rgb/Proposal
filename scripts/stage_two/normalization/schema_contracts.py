"""Normalized event schema contract loading and registration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import NORMALIZED_SCHEMA_PATH as CONFIG_NORMALIZED_SCHEMA_PATH
from scripts.db import session_scope
from scripts.db.models import SchemaVersion


DEFAULT_NORMALIZED_SCHEMA_PATH = Path(CONFIG_NORMALIZED_SCHEMA_PATH)


@dataclass(frozen=True)
class NormalizedSchemaContract:
    """Loaded normalized schema contract metadata."""

    path: Path
    payload: dict[str, Any]
    sha256: str


class NormalizedSchemaRegistry:
    """Register normalized schema contracts in `schema_versions`."""

    def __init__(self, session: Session) -> None:
        """Initialize the registry with an externally managed session."""
        self.session = session

    def load_contract(
        self,
        schema_path: str | Path = DEFAULT_NORMALIZED_SCHEMA_PATH,
    ) -> NormalizedSchemaContract:
        """Load a normalized schema contract from JSON."""
        path = Path(schema_path)
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        return NormalizedSchemaContract(
            path=path,
            payload=payload,
            sha256=hashlib.sha256(raw).hexdigest(),
        )

    def register_contract(
        self,
        schema_path: str | Path = DEFAULT_NORMALIZED_SCHEMA_PATH,
    ) -> SchemaVersion:
        """Register or update the normalized schema contract without committing."""
        contract = self.load_contract(schema_path)
        payload = contract.payload
        statement = select(SchemaVersion).where(
            SchemaVersion.schema_name == payload["schema_name"],
            SchemaVersion.schema_version == payload["schema_version"],
            SchemaVersion.layer == payload["layer"],
            SchemaVersion.branch.is_(None),
        )
        existing = self.session.execute(statement).scalar_one_or_none()
        if existing is None:
            existing = SchemaVersion(
                schema_name=payload["schema_name"],
                schema_version=payload["schema_version"],
                layer=payload["layer"],
                branch=None,
            )
            self.session.add(existing)

        existing.schema_path = str(contract.path)
        existing.schema_hash_sha256 = contract.sha256
        existing.is_active = True
        existing.description = payload.get("description")
        existing.columns_json = {
            "fields": payload.get("fields", []),
            "null_policy": payload.get("null_policy", {}),
        }
        self.session.flush()
        return existing


def register_default_normalized_schema() -> SchemaVersion:
    """Register the default normalized event schema in a managed transaction."""
    with session_scope() as session:
        return NormalizedSchemaRegistry(session).register_contract()
