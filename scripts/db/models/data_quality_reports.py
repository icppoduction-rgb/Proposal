"""Data quality and leakage report catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from scripts.db.models.base import Base
from scripts.db.models.constants import (
    QUALITY_ARTIFACT_TYPE_VALUES,
    QUALITY_SEVERITY_VALUES,
    QUALITY_STATUS_VALUES,
    sql_in,
)


class DataQualityReport(Base):
    """Quality, normalization, schema mismatch, and leakage check result."""

    __tablename__ = "data_quality_reports"
    __table_args__ = (
        CheckConstraint(
            f"artifact_type IN ({sql_in(QUALITY_ARTIFACT_TYPE_VALUES)})",
            name="artifact_type_valid",
        ),
        CheckConstraint(f"status IN ({sql_in(QUALITY_STATUS_VALUES)})", name="status_valid"),
        CheckConstraint(f"severity IN ({sql_in(QUALITY_SEVERITY_VALUES)})", name="severity_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    artifact_type: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_id: Mapped[int | None] = mapped_column(BigInteger)
    check_group: Mapped[str] = mapped_column(Text, nullable=False)
    check_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False, server_default="INFO")
    rows_total: Mapped[int | None] = mapped_column(BigInteger)
    rows_valid: Mapped[int | None] = mapped_column(BigInteger)
    rows_failed: Mapped[int | None] = mapped_column(BigInteger)
    missing_values_count: Mapped[int | None] = mapped_column(BigInteger)
    duplicate_rows_count: Mapped[int | None] = mapped_column(BigInteger)
    schema_mismatch_count: Mapped[int | None] = mapped_column(BigInteger)
    leakage_issue_count: Mapped[int | None] = mapped_column(BigInteger)
    label_distribution_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    timestamp_coverage_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    report_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
