"""add stage three blocking artifact statuses."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "7c9a4e2b1d30"
down_revision: str | None = "6b7f0c2d4a91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_VALUES = (
    "'PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', "
    "'BLOCKED', 'BLOCKED_BY_LEAKAGE', 'BLOCKED_BY_QUALITY'"
)
OLD_VALUES = "'PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'BLOCKED'"

TABLES = (
    "normalized_artifacts",
    "feature_artifacts",
    "preprocessing_artifacts",
    "model_ready_artifacts",
)


def upgrade() -> None:
    """Allow Stage Three-specific blocking statuses on artifact tables."""
    for table_name in TABLES:
        _replace_status_constraint(table_name, NEW_VALUES)


def downgrade() -> None:
    """Restore the previous generic artifact status constraint."""
    for table_name in TABLES:
        _replace_status_constraint(table_name, OLD_VALUES)


def _replace_status_constraint(table_name: str, values: str) -> None:
    constraint_name = op.f(f"ck_{table_name}_status_valid")
    op.drop_constraint(constraint_name, table_name, type_="check")
    op.create_check_constraint(
        constraint_name,
        table_name,
        f"status IN ({values})",
    )
