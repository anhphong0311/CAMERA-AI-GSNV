"""
ORM model: performance_scores.

Tổng hợp thời lượng hành vi và điểm hiệu suất theo ngày/nhân viên.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class PerformanceScore(Base, TimestampMixin):
    """
    Điểm hiệu suất hàng ngày cho từng nhân viên.

    breakdown: JSON chi tiết thời lượng từng loại hành vi.
    score: 0–100, tính bởi scheduler (sprint sau).
    """

    __tablename__ = "performance_scores"
    __table_args__ = (UniqueConstraint("employee_id", "day", name="uq_perf_employee_day"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    working_s: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    phone_s: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    talking_s: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_s: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    idle_s: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eating_s: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    employee: Mapped["Employee"] = relationship(back_populates="performance_scores")
