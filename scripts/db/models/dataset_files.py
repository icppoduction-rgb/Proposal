"""Raw dataset file catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, FILE_STATUS_VALUES, ROLE_VALUES, sql_in


class DatasetFile(Base):
    """One raw file registered in the PostgreSQL catalog."""

    __tablename__ = "dataset_files"
    __table_args__ = (
        UniqueConstraint("dataset_id", "file_path", name="uq_dataset_files_dataset_id_file_path"),
        CheckConstraint(f"role IN ({sql_in(ROLE_VALUES)})", name="role_valid"),
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(f"status IN ({sql_in(FILE_STATUS_VALUES)})", name="status_valid"),
        Index("idx_dataset_files_dataset_id", "dataset_id"),
        Index("idx_dataset_files_role_branch", "role", "branch"),
        Index("idx_dataset_files_source_format", "source_format"),
        Index("idx_dataset_files_status", "status"),
        Index("idx_dataset_files_hash", "file_hash_sha256"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    ingestion_run_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_runs.id"))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    relative_path: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[str | None] = mapped_column(Text)
    source_format: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    file_hash_sha256: Mapped[str | None] = mapped_column(Text)
    file_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    role: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="REGISTERED")
    parser_hint: Mapped[str | None] = mapped_column(Text)
    has_embedded_label: Mapped[bool | None] = mapped_column(Boolean)
    label_source_hint: Mapped[str | None] = mapped_column(Text)
    timestamp_source_hint: Mapped[str | None] = mapped_column(Text)
    encoding_hint: Mapped[str | None] = mapped_column(Text)
    compression_hint: Mapped[str | None] = mapped_column(Text)
    row_count_hint: Mapped[int | None] = mapped_column(BigInteger)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="files")
    ingestion_run: Mapped["IngestionRun | None"] = relationship(back_populates="files")
    parser_runs: Mapped[list["ParserRun"]] = relationship(back_populates="file")
    normalized_artifacts: Mapped[list["NormalizedArtifact"]] = relationship(back_populates="file")
