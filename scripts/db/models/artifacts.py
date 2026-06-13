"""Artifact registry models for normalized, feature, and model-ready outputs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import (
    BRANCH_VALUES,
    MODEL_READY_DATA_TYPE_VALUES,
    ROLE_VALUES,
    RUN_STATUS_VALUES,
    sql_in,
)


class NormalizedArtifact(Base):
    """Normalized Parquet artifact registered after a parser run."""

    __tablename__ = "normalized_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "parser_run_id",
            "normalized_path",
            name="uq_normalized_artifacts_parser_run_id_normalized_path",
        ),
        CheckConstraint(f"role IN ({sql_in(ROLE_VALUES)})", name="role_valid"),
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(f"status IN ({sql_in(RUN_STATUS_VALUES)})", name="status_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey("dataset_files.id"), nullable=False)
    parser_run_id: Mapped[int] = mapped_column(ForeignKey("parser_runs.id"), nullable=False)
    schema_version_id: Mapped[int | None] = mapped_column(ForeignKey("schema_versions.id"))
    role: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    modality: Mapped[str] = mapped_column(Text, nullable=False)
    source_format: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_path: Mapped[str] = mapped_column(Text, nullable=False)
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int | None] = mapped_column(BigInteger)
    event_count: Mapped[int | None] = mapped_column(BigInteger)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    content_hash_sha256: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="SUCCESS")
    null_counts_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    label_distribution_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    min_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="normalized_artifacts")
    file: Mapped["DatasetFile"] = relationship(back_populates="normalized_artifacts")
    parser_run: Mapped["ParserRun"] = relationship(back_populates="normalized_artifacts")
    schema: Mapped["SchemaVersion | None"] = relationship(back_populates="normalized_artifacts")
    feature_artifacts: Mapped[list["FeatureArtifact"]] = relationship(
        back_populates="normalized_artifact"
    )


class FeatureArtifact(Base):
    """Feature Parquet artifact registered after feature extraction."""

    __tablename__ = "feature_artifacts"
    __table_args__ = (
        CheckConstraint(f"role IN ({sql_in(ROLE_VALUES)})", name="role_valid"),
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(f"status IN ({sql_in(RUN_STATUS_VALUES)})", name="status_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    normalized_artifact_id: Mapped[int | None] = mapped_column(ForeignKey("normalized_artifacts.id"))
    role: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    feature_group: Mapped[str] = mapped_column(Text, nullable=False)
    feature_path: Mapped[str] = mapped_column(Text, nullable=False)
    feature_schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int | None] = mapped_column(BigInteger)
    sample_count: Mapped[int | None] = mapped_column(BigInteger)
    feature_count: Mapped[int | None] = mapped_column(Integer)
    entity_count: Mapped[int | None] = mapped_column(BigInteger)
    window_size_seconds: Mapped[int | None] = mapped_column(Integer)
    window_step_seconds: Mapped[int | None] = mapped_column(Integer)
    label_distribution_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    excluded_columns_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="SUCCESS")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="feature_artifacts")
    normalized_artifact: Mapped["NormalizedArtifact | None"] = relationship(
        back_populates="feature_artifacts"
    )
    preprocessing_artifacts: Mapped[list["PreprocessingArtifact"]] = relationship(
        back_populates="fitted_on_feature_artifact"
    )
    model_ready_artifacts: Mapped[list["ModelReadyArtifact"]] = relationship(
        back_populates="feature_artifact"
    )


class ModelReadyArtifact(Base):
    """Final model-ready artifact registry entry."""

    __tablename__ = "model_ready_artifacts"
    __table_args__ = (
        CheckConstraint(f"role IN ({sql_in(ROLE_VALUES)})", name="role_valid"),
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(
            f"data_type IN ({sql_in(MODEL_READY_DATA_TYPE_VALUES)})",
            name="data_type_valid",
        ),
        CheckConstraint(f"status IN ({sql_in(RUN_STATUS_VALUES)})", name="status_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    artifact_uid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    feature_artifact_id: Mapped[int | None] = mapped_column(ForeignKey("feature_artifacts.id"))
    preprocessing_artifact_id: Mapped[int | None] = mapped_column(
        ForeignKey("preprocessing_artifacts.id")
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    data_type: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    sample_count: Mapped[int | None] = mapped_column(BigInteger)
    feature_count: Mapped[int | None] = mapped_column(Integer)
    label_distribution_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    excluded_columns_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    sequence_length: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="SUCCESS")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    feature_artifact: Mapped["FeatureArtifact | None"] = relationship(
        back_populates="model_ready_artifacts"
    )
    preprocessing_artifact: Mapped["PreprocessingArtifact | None"] = relationship(
        back_populates="model_ready_artifacts"
    )
