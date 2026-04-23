from __future__ import annotations

from alembic import op

from backend.app.db.init_db import _ensure_runtime_columns
from cybersec_platform.db import Base

# revision identifiers, used by Alembic.
revision = "0001_baseline_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    _ensure_runtime_columns(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
