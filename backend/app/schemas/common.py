"""
Schema response chuẩn hóa cho toàn bộ API.

Mọi endpoint trả về cùng format { data, meta, error } theo thiết kế API doc.
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Chi tiết lỗi trong response."""

    code: str = Field(..., description="Mã lỗi machine-readable")
    message: str = Field(..., description="Thông báo lỗi cho người dùng")


class PaginationMeta(BaseModel):
    """Metadata phân trang."""

    total: int = Field(..., description="Tổng số bản ghi")
    page: int = Field(default=1, description="Trang hiện tại")
    size: int = Field(default=20, description="Số bản ghi mỗi trang")


class ApiResponse(BaseModel, Generic[T]):
    """
    Wrapper response chuẩn AEMS.

    Generic T cho phép type-safe data payload.
    """

    data: Optional[T] = Field(default=None, description="Payload dữ liệu")
    meta: Optional[dict[str, Any]] = Field(default=None, description="Metadata bổ sung")
    error: Optional[ErrorDetail] = Field(default=None, description="Lỗi nếu có")


class MessageResponse(BaseModel):
    """Response đơn giản chỉ chứa message — dùng cho skeleton endpoints."""

    message: str = Field(..., description="Thông báo trạng thái")


class HealthData(BaseModel):
    """Dữ liệu health check."""

    status: str = Field(..., description="healthy | degraded | unhealthy")
    postgres: bool = Field(..., description="PostgreSQL kết nối OK")
    redis: bool = Field(..., description="Redis kết nối OK")
    version: str = Field(default="1.0.0-sprint1", description="Phiên bản API")
