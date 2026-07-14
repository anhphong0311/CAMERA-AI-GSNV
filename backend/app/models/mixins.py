"""
Mixin và type helpers dùng chung cho ORM models.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Thêm cột created_at / updated_at tự động cho mọi bảng cần audit thời gian.

    created_at: thời điểm tạo bản ghi (server default now()).
    updated_at: thời điểm cập nhật gần nhất (tự cập nhật on update).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


def new_uuid() -> uuid.UUID:
    """Sinh UUID v4 cho primary key kiểu UUID."""
    return uuid.uuid4()
