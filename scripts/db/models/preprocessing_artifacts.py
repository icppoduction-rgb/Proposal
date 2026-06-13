"""Preprocessing artifact catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, RUN_STATUS_VALUES, sql_in


class PreprocessingArtifact(Base):
    """Scaler/encoder/imputer artifact fitted only on TRAIN."""

    __tablename__ = "preprocessing_artifacts"
    __table_args__ = (
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint("fitted_on_role = 'TRAIN'", name="fitted_on_role_train"),
        CheckConstraint(f"status IN ({sql_in(RUN_STATUS_VALUES)})", name="status_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    feature_group: Mapped[str | None] = mapped_column(Text)
    preprocessing_type: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    fitted_on_role: Mapped[str] = mapped_column(Text, nullable=False, server_default="TRAIN")
    fitted_on_feature_artifact_id: Mapped[int | None] = mapped_column(
        ForeignKey("feature_artifacts.id")
    )
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    object_version: Mapped[str] = mapped_column(Text, nullable=False)
    columns_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    params_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="SUCCESS")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    fitted_on_feature_artifact: Mapped["FeatureArtifact | None"] = relationship(
        back_populates="preprocessing_artifacts"
    )
    model_ready_artifacts: Mapped[list["ModelReadyArtifact"]] = relationship(
        back_populates="preprocessing_artifact"
    )
