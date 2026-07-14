"""
ORM model: logs.

Nhật ký hệ thống — audit, health, lỗi worker/API.
Tách khỏi Loguru file log để query/report qua API.
"""

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Log(Base, TimestampMixin):
    """
    Bản ghi log cấu trúc lưu DB.

    level: DEBUG | INFO | WARNING | ERROR | CRITICAL
    source: worker | api | scheduler | auth ...
    meta: JSON context bổ sung (camera_id, track_id...).
    """

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
