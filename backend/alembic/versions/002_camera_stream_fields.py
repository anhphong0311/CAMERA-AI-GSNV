"""Alembic migration 002 — bổ sung trường stream cho bảng cameras."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm location, last_online, last_heartbeat."""
    op.add_column("cameras", sa.Column("location", sa.String(length=255), nullable=True))
    op.add_column(
        "cameras",
        sa.Column("last_online", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cameras",
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Rollback cột Sprint 2."""
    op.drop_column("cameras", "last_heartbeat")
    op.drop_column("cameras", "last_online")
    op.drop_column("cameras", "location")
