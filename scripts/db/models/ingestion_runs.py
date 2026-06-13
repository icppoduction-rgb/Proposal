"""Ingestion run catalog model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, ROLE_VALUES, sql_in

INGESTION_RUN_STATUS_VALUES: tuple[str, ...] = (
    "RUNNING",
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "FAILED",
    "SKIPPED",
)


class IngestionRun(Base):
    """A directory scanning run that registers raw files in the catalog."""

    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({sql_in(INGESTION_RUN_STATUS_VALUES)})",
            name="status_valid",
        ),
        CheckConstraint(
            f"branch IS NULL OR branch IN ({sql_in(BRANCH_VALUES)})",
            name="branch_valid",
        ),
        CheckConstraint(
            f"role IS NULL OR role IN ({sql_in(ROLE_VALUES)})",
            name="role_valid",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    root_path: Mapped[str] = mapped_column(Text, nullable=False)
    root_path_kind: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="RUNNING")
    files_seen: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    files_new: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    files_existing: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    files_changed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    files_failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)
    report_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    files: Mapped[list["DatasetFile"]] = relationship(back_populates="ingestion_run")
