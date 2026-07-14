"""
ORM model: rules.

Lưu cấu hình Rule Engine — ngưỡng, scope, bật/tắt.
Logic rule chạy ở ai-worker (sprint sau); DB chỉ persist config.
"""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert


class Rule(Base, TimestampMixin):
    """
    Định nghĩa rule hành vi (phone_usage, away, ...).

    params: JSON chứa on_seconds, off_seconds, cooldown, ngưỡng AI...
    scope: JSON cameras/rois/time_windows áp dụng.
    """

    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    score_weight: Mapped[float] = mapped_column(
        Numeric(5, 2), default=1.0, nullable=False
    )
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    scope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    alerts: Mapped[List["Alert"]] = relationship(back_populates="rule")
