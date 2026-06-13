"""Repository for label mapping rules."""

from __future__ import annotations

from sqlalchemy import select

from scripts.db.models import LabelMappingRule
from scripts.db.repositories.base_repository import BaseRepository


class LabelRepository(BaseRepository[LabelMappingRule]):
    """Data access methods for `label_mapping_rules`."""

    model = LabelMappingRule

    def list_active_rules(self, *, branch: str | None = None) -> list[LabelMappingRule]:
        """Return active label mapping rules ordered by priority."""
        statement = select(LabelMappingRule).where(LabelMappingRule.is_active.is_(True))
        if branch is not None:
            statement = statement.where(LabelMappingRule.branch == branch)
        statement = statement.order_by(LabelMappingRule.priority.asc(), LabelMappingRule.id.asc())
        return list(self.session.execute(statement).scalars())

    def find_matching_rules(
        self,
        *,
        branch: str,
        role: str | None = None,
        source_format: str | None = None,
    ) -> list[LabelMappingRule]:
        """Return active rules matching branch plus optional role/source_format."""
        statement = select(LabelMappingRule).where(
            LabelMappingRule.is_active.is_(True),
            LabelMappingRule.branch == branch,
        )
        if role is not None:
            statement = statement.where(
                (LabelMappingRule.role == role) | (LabelMappingRule.role.is_(None))
            )
        if source_format is not None:
            statement = statement.where(
                (LabelMappingRule.source_format == source_format)
                | (LabelMappingRule.source_format.is_(None))
            )
        statement = statement.order_by(LabelMappingRule.priority.asc(), LabelMappingRule.id.asc())
        return list(self.session.execute(statement).scalars())

    def register_rule(self, rule: LabelMappingRule) -> LabelMappingRule:
        """Register a label mapping rule without committing."""
        return self.add(rule)
