"""
ORM model: alerts, snapshots, videos, notifications.

alert — cảnh báo khi rule kích hoạt.
snapshot / video — bằng chứng đính kèm alert.
notifications — log gửi Telegram (sprint sau).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.employee import Employee
    from app.models.rule import Rule
    from app.models.tracking import Tracking
    from app.models.zone import Zone


class Alert(Base, TimestampMixin):
    """
    Cảnh báo hành vi — output của Rule Engine.

    reason: JSON mô tả điều kiện nào đã kích hoạt (audit/minh bạch).
    dedup_key: chống trùng alert cùng track+rule trong cửa sổ thời gian.
    """

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    rule_id: Mapped[str] = mapped_column(
        ForeignKey("rules.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"), nullable=True
    )
    tracking_id: Mapped[int | None] = mapped_column(
        ForeignKey("trackings.id", ondelete="SET NULL"), nullable=True
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    dedup_key: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)

    rule: Mapped["Rule"] = relationship(back_populates="alerts")
    camera: Mapped["Camera"] = relationship(back_populates="alerts")
    zone: Mapped["Zone | None"] = relationship(back_populates="alerts")
    tracking: Mapped["Tracking | None"] = relationship(back_populates="alerts")
    employee: Mapped["Employee | None"] = relationship(back_populates="alerts")
    snapshots: Mapped[List["Snapshot"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )
    videos: Mapped[List["Video"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )


class Snapshot(Base, TimestampMixin):
    """Ảnh chụp bằng chứng tại thời điểm vi phạm — lưu key object storage."""

    __tablename__ = "snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    alert: Mapped["Alert"] = relationship(back_populates="snapshots")


class Video(Base, TimestampMixin):
    """Video clip bằng chứng (pre/post-roll) — lưu key object storage."""

    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    duration_s: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    codec: Mapped[str | None] = mapped_column(String(20), nullable=True)

    alert: Mapped["Alert"] = relationship(back_populates="videos")


class Notification(Base, TimestampMixin):
    """
    Log thông báo gửi đi (Telegram sprint sau).

    status: pending | sent | failed — hỗ trợ retry queue.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(20), default="telegram", nullable=False)
    target: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    alert: Mapped["Alert"] = relationship(back_populates="notifications")
