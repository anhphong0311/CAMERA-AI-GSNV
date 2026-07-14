"""
Pydantic schemas — Camera API request/response.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CameraBase(BaseModel):
    """Fields chung create/update camera."""

    code: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=150)
    location: Optional[str] = Field(None, max_length=255)
    rtsp_main: str = Field(..., description="RTSP URL main stream")
    rtsp_sub: Optional[str] = Field(None, description="RTSP URL sub stream (ưu tiên cho grabber)")
    department_id: Optional[int] = None
    resolution: Optional[str] = Field(None, max_length=20)
    fps: int = Field(default=15, ge=1, le=60)
    enabled: bool = True


class CameraCreate(CameraBase):
    """Body POST /cameras."""


class CameraUpdate(BaseModel):
    """Body PUT /cameras/{id} — tất cả optional."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = None
    location: Optional[str] = None
    rtsp_main: Optional[str] = None
    rtsp_sub: Optional[str] = None
    department_id: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[int] = Field(None, ge=1, le=60)
    enabled: Optional[bool] = None


class CameraRead(CameraBase):
    """Response đọc camera từ DB."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    last_online: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    worker_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @property
    def rtsp_url(self) -> str:
        """URL ưu tiên sub stream — helper, không serialize mặc định."""
        return self.rtsp_sub or self.rtsp_main


class CameraHealthRead(BaseModel):
    """Response GET /cameras/{id}/health."""

    camera_id: int
    db_status: str
    runtime: dict[str, Any]
    last_online: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None


class CameraFPSRead(BaseModel):
    """Response GET /cameras/{id}/fps."""

    camera_id: int
    current_fps: float
    average_fps: float
    read_time_ms: float
    decode_time_ms: float
    queue_size: int
    target_fps: int


class CameraFrameRead(BaseModel):
    """Response GET /cameras/{id}/frame — JPEG base64."""

    camera_id: int
    frame_id: int
    timestamp: datetime
    width: int
    height: int
    content_type: str = "image/jpeg"
    image_base64: str
