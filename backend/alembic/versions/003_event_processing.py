"""Alembic migration 003 — bảng Event Processing Center (Sprint 7)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tạo event_records / event_notifications / event_retries."""
    op.create_table(
        "event_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("camera_id", sa.Integer(), nullable=False),
        sa.Column("camera_name", sa.String(length=150), nullable=True),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="NEW"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("roi", sa.String(length=100), nullable=True),
        sa.Column("snapshot_path", sa.Text(), nullable=True),
        sa.Column("video_path", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_event_records_event_id", "event_records", ["event_id"], unique=True)
    op.create_index("ix_event_records_camera_id", "event_records", ["camera_id"])
    op.create_index("ix_event_records_track_id", "event_records", ["track_id"])
    op.create_index("ix_event_records_rule_id", "event_records", ["rule_id"])

    op.create_table(
        "event_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_pk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="telegram"),
        sa.Column("target", sa.String(length=150), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_pk"], ["event_records.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "event_retries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("notification_pk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("delay_s", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["notification_pk"], ["event_notifications.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    """Rollback Sprint 7."""
    op.drop_table("event_retries")
    op.drop_table("event_notifications")
    op.drop_index("ix_event_records_rule_id", table_name="event_records")
    op.drop_index("ix_event_records_track_id", table_name="event_records")
    op.drop_index("ix_event_records_camera_id", table_name="event_records")
    op.drop_index("ix_event_records_event_id", table_name="event_records")
    op.drop_table("event_records")
