"""Repository for schema version records."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from scripts.db.models import SchemaVersion
from scripts.db.repositories.base_repository import BaseRepository


class SchemaRepository(BaseRepository[SchemaVersion]):
    """Data access methods for `schema_versions`."""

    model = SchemaVersion

    def get_active(
        self,
        *,
        schema_name: str,
        layer: str,
        branch: str | None = None,
    ) -> SchemaVersion | None:
        """Return the active schema version for a schema/layer/branch."""
        statement = select(SchemaVersion).where(
            SchemaVersion.schema_name == schema_name,
            SchemaVersion.layer == layer,
            SchemaVersion.branch.is_(branch) if branch is None else SchemaVersion.branch == branch,
            SchemaVersion.is_active.is_(True),
        )
        return self.session.execute(statement).scalar_one_or_none()

    def register_schema_version(self, **values: Any) -> SchemaVersion:
        """Register a schema version without committing."""
        schema_version = SchemaVersion(**values)
        return self.add(schema_version)
