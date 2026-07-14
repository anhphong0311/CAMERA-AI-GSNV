"""
ORM models cho module Enterprise Admin (Sprint 9).

Bảng độc lập, không thêm ràng buộc khoá ngoại tới bảng của module khác (tuân thủ
"không truy cập trực tiếp DB module khác"). Cấu hình/audit/model/session/backup/job
đều lưu Database (không hardcode).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class AuditLog(Base, TimestampMixin):
    """Nhật ký kiểm toán — ghi mọi hành động quan trọng."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    module: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    target: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ConfigEntry(Base, TimestampMixin):
    """Cấu hình hệ thống lưu DB (Configuration Center)."""

    __tablename__ = "config_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ModelVersion(Base, TimestampMixin):
    """Phiên bản AI model (AI Model Management) — chỉ metadata, không đổi engine."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="inactive", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class UserSession(Base, TimestampMixin):
    """Phiên đăng nhập (refresh token rotation, logout all devices)."""

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    refresh_jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    access_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class BackupRecord(Base, TimestampMixin):
    """Bản ghi Backup (DB/Config/Rule/ROI/AI Config)."""

    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ScheduledJobRecord(Base, TimestampMixin):
    """Cấu hình + trạng thái job định kỳ (Scheduler)."""

    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
