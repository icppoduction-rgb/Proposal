"""Parser registry catalog model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, ROLE_VALUES, sql_in


class ParserRegistry(Base):
    """Available parser strategies and routing metadata."""

    __tablename__ = "parser_registry"
    __table_args__ = (
        UniqueConstraint(
            "parser_name",
            "parser_version",
            "branch",
            "source_format",
            "supported_role",
            name="uq_parser_registry_parser_name_parser_version",
        ),
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(
            f"supported_role IS NULL OR supported_role IN ({sql_in(ROLE_VALUES)})",
            name="supported_role_valid",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parser_name: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    source_format: Mapped[str] = mapped_column(Text, nullable=False)
    supported_role: Mapped[str | None] = mapped_column(Text)
    normalized_schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    parser_module: Mapped[str] = mapped_column(Text, nullable=False)
    parser_class: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    supports_streaming: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    requires_external_tools: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    external_tools_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
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

    parser_runs: Mapped[list["ParserRun"]] = relationship(back_populates="parser_registry")
