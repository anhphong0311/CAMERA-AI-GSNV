"""
ORM models cho Event Processing Center (Sprint 7).

Bảng độc lập (không FK cứng tới rules/cameras) để module tách biệt:
- event_records: bản ghi xử lý event + tham chiếu evidence.
- event_notifications: log gửi notification.
- event_retries: lịch sử retry.
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class EventRecordORM(Base, TimestampMixin):
    """Bản ghi xử lý một BehaviorEvent."""

    __tablename__ = "event_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    camera_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    camera_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    track_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi: Mapped[str | None] = mapped_column(String(100), nullable=True)
    snapshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    notifications: Mapped[List["EventNotificationORM"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class EventNotificationORM(Base, TimestampMixin):
    """Log gửi notification cho một event."""

    __tablename__ = "event_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    event_pk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(20), default="telegram", nullable=False)
    target: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    event: Mapped["EventRecordORM"] = relationship(back_populates="notifications")
    retries: Mapped[List["EventRetryORM"]] = relationship(
        back_populates="notification", cascade="all, delete-orphan"
    )


class EventRetryORM(Base, TimestampMixin):
    """Lịch sử retry của một notification."""

    __tablename__ = "event_retries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    notification_pk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_notifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    notification: Mapped["EventNotificationORM"] = relationship(back_populates="retries")
