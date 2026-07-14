"""
ORM model: trackings, detections.

trackings — phiên theo dõi một person (ByteTrack ID) trên camera.
detections — bản ghi phát hiện AI (sampled, volume cao).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.camera import Camera
    from app.models.employee import Employee
    from app.models.zone import Zone


class Tracking(Base, TimestampMixin):
    """
    Phiên tracking — gắn track_key (ByteTrack) với camera trong khoảng thời gian.

    Một person xuất hiện → tracking mới; rời khung → ended_at được set.
    """

    __tablename__ = "trackings"
    __table_args__ = (
        UniqueConstraint("camera_id", "track_key", "started_at", name="uq_tracking_session"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_key: Mapped[int] = mapped_column(BigInteger, nullable=False)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)

    camera: Mapped["Camera"] = relationship(back_populates="trackings")
    employee: Mapped["Employee | None"] = relationship(back_populates="trackings")
    zone: Mapped["Zone | None"] = relationship(back_populates="trackings")
    detections: Mapped[List["Detection"]] = relationship(
        back_populates="tracking", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(back_populates="tracking")


class Detection(Base):
    """
    Bản ghi detection từ AI pipeline — lưu sampled (1-2 fps).

    Sprint 1: chỉ schema; dữ liệu thật từ ai-worker ở sprint sau.
    """

    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tracking_id: Mapped[int | None] = mapped_column(
        ForeignKey("trackings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ts: Mapped[datetime] = mapped_column(nullable=False, index=True)
    cls: Mapped[str] = mapped_column(String(30), nullable=False)
    bbox: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    conf: Mapped[float | None] = mapped_column(Float, nullable=True)
    keypoints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    tracking: Mapped["Tracking | None"] = relationship(back_populates="detections")
