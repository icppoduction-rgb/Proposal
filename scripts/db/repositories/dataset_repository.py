"""Repository for dataset catalog records."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from scripts.db.models import Dataset
from scripts.db.repositories.base_repository import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Data access methods for `datasets`."""

    model = Dataset

    def get_by_name_branch_role(self, name: str, branch: str, role: str) -> Dataset | None:
        """Return a dataset by its natural name/branch/role key."""
        statement = select(Dataset).where(
            Dataset.name == name,
            Dataset.branch == branch,
            Dataset.role == role,
        )
        return self.session.execute(statement).scalar_one_or_none()

    def get_or_create_dataset(
        self,
        *,
        name: str,
        slug: str,
        branch: str,
        role: str,
        **values: Any,
    ) -> tuple[Dataset, bool]:
        """Get an existing dataset or create a new one without committing."""
        existing = self.get_by_name_branch_role(name, branch, role)
        if existing is not None:
            return existing, False

        dataset = Dataset(name=name, slug=slug, branch=branch, role=role, **values)
        self.session.add(dataset)
        self.session.flush()
        return dataset, True

    def list_active(self) -> list[Dataset]:
        """Return all active datasets."""
        statement = select(Dataset).where(Dataset.is_active.is_(True)).order_by(Dataset.id)
        return list(self.session.execute(statement).scalars())
