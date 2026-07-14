"""
ORM model: departments, employees.

departments — phòng ban tổ chức.
employees — nhân viên được giám sát (map tới zone/bàn làm việc).
"""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.camera import Camera, Zone
    from app.models.performance_score import PerformanceScore
    from app.models.tracking import Tracking


class Department(Base, TimestampMixin):
    """Phòng ban — nhóm nhân viên và camera theo khu vực."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    manager_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    employees: Mapped[List["Employee"]] = relationship(back_populates="department")
    cameras: Mapped[List["Camera"]] = relationship(back_populates="department")


class Employee(Base, TimestampMixin):
    """
    Nhân viên văn phòng — đối tượng giám sát chính.

    zone_id: bàn làm việc cố định (ROI/zone) để map tracking → nhân viên.
    """

    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department | None"] = relationship(back_populates="employees")
    zone: Mapped["Zone | None"] = relationship(back_populates="employee")
    trackings: Mapped[List["Tracking"]] = relationship(back_populates="employee")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="employee")
    performance_scores: Mapped[List["PerformanceScore"]] = relationship(
        back_populates="employee"
    )
