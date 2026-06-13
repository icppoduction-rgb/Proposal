"""Parser run history model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import PARSER_RUN_STATUS_VALUES, sql_in


class ParserRun(Base):
    """One parsing and normalization attempt for a registered raw file."""

    __tablename__ = "parser_runs"
    __table_args__ = (
        CheckConstraint(f"status IN ({sql_in(PARSER_RUN_STATUS_VALUES)})", name="status_valid"),
        Index("idx_parser_runs_file_id", "file_id"),
        Index("idx_parser_runs_status", "status"),
        Index("idx_parser_runs_parser", "parser_name", "parser_version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("dataset_files.id"), nullable=False)
    parser_registry_id: Mapped[int | None] = mapped_column(ForeignKey("parser_registry.id"))
    parser_name: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version_id: Mapped[int | None] = mapped_column(ForeignKey("schema_versions.id"))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="RUNNING")
    rows_read: Mapped[int | None] = mapped_column(BigInteger)
    rows_parsed: Mapped[int | None] = mapped_column(BigInteger)
    rows_failed: Mapped[int | None] = mapped_column(BigInteger)
    events_emitted: Mapped[int | None] = mapped_column(BigInteger)
    output_parquet_path: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    report_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    file: Mapped["DatasetFile"] = relationship(back_populates="parser_runs")
    parser_registry: Mapped["ParserRegistry | None"] = relationship(back_populates="parser_runs")
    schema_version: Mapped["SchemaVersion | None"] = relationship(back_populates="parser_runs")
    normalized_artifacts: Mapped[list["NormalizedArtifact"]] = relationship(back_populates="parser_run")
