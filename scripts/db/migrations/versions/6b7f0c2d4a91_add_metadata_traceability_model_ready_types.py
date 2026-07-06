"""add metadata and traceability model-ready data types."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "6b7f0c2d4a91"
down_revision: str | None = "5a38996dff5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_VALUES = "'X', 'y', 'metadata', 'traceability', 'sequence', 'split_index', 'preprocessing_metadata'"
OLD_VALUES = "'X', 'y', 'sequence', 'split_index', 'preprocessing_metadata'"


def upgrade() -> None:
    """Allow separate metadata and traceability model-ready catalog rows."""
    op.drop_constraint(
        op.f("ck_model_ready_artifacts_data_type_valid"),
        "model_ready_artifacts",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_model_ready_artifacts_data_type_valid"),
        "model_ready_artifacts",
        f"data_type IN ({NEW_VALUES})",
    )


def downgrade() -> None:
    """Restore the previous model-ready data type constraint."""
    op.drop_constraint(
        op.f("ck_model_ready_artifacts_data_type_valid"),
        "model_ready_artifacts",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_model_ready_artifacts_data_type_valid"),
        "model_ready_artifacts",
        f"data_type IN ({OLD_VALUES})",
    )
