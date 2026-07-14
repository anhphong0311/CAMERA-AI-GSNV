"""ORM models — ML Platform (Sprint 13)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MLDataset(Base, TimestampMixin):
    __tablename__ = "ml_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="image", nullable=False)
    tags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class MLDatasetVersion(Base, TimestampMixin):
    __tablename__ = "ml_dataset_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    split_train: Mapped[float] = mapped_column(Float, default=0.8)
    split_val: Mapped[float] = mapped_column(Float, default=0.1)
    split_test: Mapped[float] = mapped_column(Float, default=0.1)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class MLTrainingJob(Base, TimestampMixin):
    __tablename__ = "ml_training_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    architecture: Mapped[str] = mapped_column(String(30), default="yolo11")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_epoch: Mapped[int] = mapped_column(Integer, default=0)
    total_epochs: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class MLTrainingEpoch(Base):
    __tablename__ = "ml_training_epochs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    loss: Mapped[float] = mapped_column(Float, default=0.0)
    val_loss: Mapped[float] = mapped_column(Float, default=0.0)
    precision: Mapped[float] = mapped_column(Float, default=0.0)
    recall: Mapped[float] = mapped_column(Float, default=0.0)
    map50: Mapped[float] = mapped_column(Float, default=0.0)
    map50_95: Mapped[float] = mapped_column(Float, default=0.0)
    gpu_mem_mb: Mapped[float] = mapped_column(Float, default=0.0)
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MLFpFnCase(Base, TimestampMixin):
    __tablename__ = "ml_fp_fn_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_type: Mapped[str] = mapped_column(String(20), nullable=False)
    media_path: Mapped[str] = mapped_column(String(500), nullable=False)
    prediction: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ground_truth: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    camera_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    marked_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
