"""Alembic migration 005 — ML Platform tables (Sprint 13 / v2.0)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
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
    op.create_table(
        "ml_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="image"),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_table(
        "ml_dataset_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("split_train", sa.Float(), server_default="0.8"),
        sa.Column("split_val", sa.Float(), server_default="0.1"),
        sa.Column("split_test", sa.Float(), server_default="0.1"),
        sa.Column("item_count", sa.Integer(), server_default="0"),
        sa.Column("notes", sa.Text(), server_default=""),
        *_timestamps(),
    )
    op.create_index("ix_ml_dataset_versions_dataset_id", "ml_dataset_versions", ["dataset_id"])

    op.create_table(
        "ml_training_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("dataset_version_id", sa.String(36), nullable=False),
        sa.Column("architecture", sa.String(30), server_default="yolo11"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("output_path", sa.String(500), nullable=True),
        sa.Column("progress", sa.Float(), server_default="0"),
        sa.Column("current_epoch", sa.Integer(), server_default="0"),
        sa.Column("total_epochs", sa.Integer(), server_default="0"),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )

    op.create_table(
        "ml_training_epochs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("epoch", sa.Integer(), nullable=False),
        sa.Column("loss", sa.Float(), server_default="0"),
        sa.Column("val_loss", sa.Float(), server_default="0"),
        sa.Column("precision", sa.Float(), server_default="0"),
        sa.Column("recall", sa.Float(), server_default="0"),
        sa.Column("map50", sa.Float(), server_default="0"),
        sa.Column("map50_95", sa.Float(), server_default="0"),
        sa.Column("gpu_mem_mb", sa.Float(), server_default="0"),
        sa.Column("duration_s", sa.Float(), server_default="0"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ml_training_epochs_job_id", "ml_training_epochs", ["job_id"])

    op.create_table(
        "ml_fp_fn_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_type", sa.String(20), nullable=False),
        sa.Column("media_path", sa.String(500), nullable=False),
        sa.Column("prediction", postgresql.JSONB(), nullable=True),
        sa.Column("ground_truth", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column("event_id", sa.String(64), nullable=True),
        sa.Column("camera_id", sa.Integer(), nullable=True),
        sa.Column("marked_by", sa.String(100), nullable=True),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("ml_fp_fn_cases")
    op.drop_index("ix_ml_training_epochs_job_id", table_name="ml_training_epochs")
    op.drop_table("ml_training_epochs")
    op.drop_table("ml_training_jobs")
    op.drop_index("ix_ml_dataset_versions_dataset_id", table_name="ml_dataset_versions")
    op.drop_table("ml_dataset_versions")
    op.drop_table("ml_datasets")
