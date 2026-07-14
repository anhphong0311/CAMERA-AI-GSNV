"""Alembic migration 004 — bảng Enterprise Admin (Sprint 9)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    """Tạo audit_logs / config_entries / model_versions / user_sessions /
    backup_records / scheduled_jobs."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_module", "audit_logs", ["module"])

    op.create_table(
        "config_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("section", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_config_entries_section", "config_entries", ["section"])
    op.create_index("ix_config_entries_key", "config_entries", ["key"], unique=True)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="inactive"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("uploaded_by", sa.String(length=100), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_model_versions_name", "model_versions", ["name"])

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("refresh_jti", sa.String(length=64), nullable=False),
        sa.Column("access_jti", sa.String(length=64), nullable=True),
        sa.Column("device", sa.String(length=200), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_refresh_jti", "user_sessions", ["refresh_jti"], unique=True)

    op.create_table(
        "backup_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_backup_records_kind", "backup_records", ["kind"])

    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="86400"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=20), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_scheduled_jobs_name", "scheduled_jobs", ["name"], unique=True)


def downgrade() -> None:
    """Rollback Sprint 9."""
    op.drop_table("scheduled_jobs")
    op.drop_table("backup_records")
    op.drop_index("ix_user_sessions_refresh_jti", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_model_versions_name", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index("ix_config_entries_key", table_name="config_entries")
    op.drop_index("ix_config_entries_section", table_name="config_entries")
    op.drop_table("config_entries")
    op.drop_index("ix_audit_logs_module", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
