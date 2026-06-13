"""Label mapping rule catalog model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Integer, Numeric, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from scripts.db.models.base import Base
from scripts.db.models.constants import BRANCH_VALUES, LABEL_STATUS_VALUES, ROLE_VALUES, sql_in


class LabelMappingRule(Base):
    """Explainable label assignment rule for normalized and feature artifacts."""

    __tablename__ = "label_mapping_rules"
    __table_args__ = (
        CheckConstraint(f"branch IN ({sql_in(BRANCH_VALUES)})", name="branch_valid"),
        CheckConstraint(
            f"role IS NULL OR role IN ({sql_in(ROLE_VALUES)})",
            name="role_valid",
        ),
        CheckConstraint("label_binary IS NULL OR label_binary IN (0, 1)", name="label_binary_valid"),
        CheckConstraint(f"label_status IN ({sql_in(LABEL_STATUS_VALUES)})", name="label_status_valid"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_uid: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    rule_name: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(Text)
    source_format: Mapped[str | None] = mapped_column(Text)
    dataset_name_pattern: Mapped[str | None] = mapped_column(Text)
    file_name_pattern: Mapped[str | None] = mapped_column(Text)
    source_field: Mapped[str | None] = mapped_column(Text)
    source_value_pattern: Mapped[str | None] = mapped_column(Text)
    label_binary: Mapped[int | None] = mapped_column(SmallInteger)
    label_family: Mapped[str | None] = mapped_column(Text)
    label_subtype: Mapped[str | None] = mapped_column(Text)
    label_source: Mapped[str] = mapped_column(Text, nullable=False)
    label_status: Mapped[str] = mapped_column(Text, nullable=False)
    label_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
