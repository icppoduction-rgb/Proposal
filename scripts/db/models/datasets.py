"""Dataset catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, ROLE_VALUES, sql_in


class Dataset(Base):
    """Dataset-level metadata for raw sources and split roles."""

    __tablename__ = "datasets"
    __table_args__ = (
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(f"role IN ({sql_in(ROLE_VALUES)})", name="role_valid"),
        UniqueConstraint("name", "branch", "role", name="uq_datasets_name_branch_role"),
        UniqueConstraint("slug", "branch", "role", name="uq_datasets_slug_branch_role"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    source_group: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    dataset_version: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    license_name: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
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

    files: Mapped[list["DatasetFile"]] = relationship(back_populates="dataset")
    normalized_artifacts: Mapped[list["NormalizedArtifact"]] = relationship(back_populates="dataset")
    feature_artifacts: Mapped[list["FeatureArtifact"]] = relationship(back_populates="dataset")
