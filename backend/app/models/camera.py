"""
ORM model: cameras, zones.

cameras — thiết bị EZVIZ C6N, lưu URL RTSP (sẽ mã hóa ở sprint sau).
zones — vùng quan tâm (ROI) đa giác trên khung hình camera.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.department import Department
    from app.models.employee import Employee
    from app.models.tracking import Tracking


class Camera(Base, TimestampMixin):
    """
    Camera IP — nguồn video RTSP cho pipeline AI (sprint sau).

    status: online | offline | lagging — cập nhật bởi health monitor.
    """

    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rtsp_main: Mapped[str] = mapped_column(Text, nullable=False)
    rtsp_sub: Mapped[str | None] = mapped_column(Text, nullable=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fps: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="offline", nullable=False)
    last_online: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    worker_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department | None"] = relationship(back_populates="cameras")
    zones: Mapped[List["Zone"]] = relationship(
        back_populates="camera", cascade="all, delete-orphan"
    )
    trackings: Mapped[List["Tracking"]] = relationship(back_populates="camera")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="camera")


class Zone(Base, TimestampMixin):
    """
    Vùng quan tâm (ROI) — đa giác normalized [0,1] trên khung hình.

    kind: desk | area | exclude | meeting — loại vùng để rule engine lọc.
    polygon: JSON array [[x,y], ...] — độc lập độ phân giải.
    """

    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kind: Mapped[str] = mapped_column(String(30), default="desk", nullable=False)
    polygon: Mapped[dict] = mapped_column(JSONB, nullable=False)

    camera: Mapped["Camera"] = relationship(back_populates="zones")
    employee: Mapped["Employee | None"] = relationship(
        back_populates="zone", uselist=False
    )
    trackings: Mapped[List["Tracking"]] = relationship(back_populates="zone")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="zone")
