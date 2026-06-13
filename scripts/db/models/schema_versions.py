"""Schema version catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, SCHEMA_LAYER_VALUES, sql_in


class SchemaVersion(Base):
    """Versioned schema contract metadata for normalized/features/model-ready layers."""

    __tablename__ = "schema_versions"
    __table_args__ = (
        UniqueConstraint(
            "schema_name",
            "schema_version",
            "layer",
            "branch",
            name="uq_schema_versions_schema_name_schema_version",
        ),
        CheckConstraint(f"layer IN ({sql_in(SCHEMA_LAYER_VALUES)})", name="layer_valid"),
        CheckConstraint(
            f"branch IS NULL OR branch IN ({sql_in(BRANCH_VALUES)})",
            name="branch_valid",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    layer: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str | None] = mapped_column(Text)
    schema_path: Mapped[str | None] = mapped_column(Text)
    schema_hash_sha256: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    description: Mapped[str | None] = mapped_column(Text)
    columns_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    parser_runs: Mapped[list["ParserRun"]] = relationship(back_populates="schema_version")
    normalized_artifacts: Mapped[list["NormalizedArtifact"]] = relationship(back_populates="schema")
