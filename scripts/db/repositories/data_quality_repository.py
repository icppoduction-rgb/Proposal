"""Repository for data quality reports."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from scripts.db.models import DataQualityReport
from scripts.db.repositories.base_repository import BaseRepository


class DataQualityRepository(BaseRepository[DataQualityReport]):
    """Data access methods for `data_quality_reports`."""

    model = DataQualityReport

    def create_report(self, **values: Any) -> DataQualityReport:
        """Create a data quality report without committing."""
        report = DataQualityReport(**values)
        return self.add(report)

    def list_failed_checks(self) -> list[DataQualityReport]:
        """Return failed or blocked quality checks."""
        statement = (
            select(DataQualityReport)
            .where(DataQualityReport.status.in_(("FAILED", "BLOCKED")))
            .order_by(DataQualityReport.created_at.desc())
        )
        return list(self.session.execute(statement).scalars())

    def get_latest_for_artifact(
        self,
        *,
        artifact_type: str,
        artifact_id: int | None,
    ) -> DataQualityReport | None:
        """Return the latest report for an artifact reference."""
        statement = (
            select(DataQualityReport)
            .where(
                DataQualityReport.artifact_type == artifact_type,
                DataQualityReport.artifact_id == artifact_id,
            )
            .order_by(DataQualityReport.created_at.desc())
            .limit(1)
        )
        return self.session.execute(statement).scalar_one_or_none()
