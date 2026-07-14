"""
Pydantic schemas cho Behavior API (request/response).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TrackIn(BaseModel):
    """Track đầu vào (từ Tracking Engine)."""

    track_id: int
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    speed_px: float = 0.0
    direction: str = "STATIONARY"
    roi: Optional[str] = None


class DetectionObjectIn(BaseModel):
    """Object ngữ cảnh (phone/cup/bottle/food/monitor/chair...)."""

    class_name: str = Field(..., alias="class")
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    confidence: float = 1.0
    class_id: int = -1

    model_config = {"populate_by_name": True}


class BehaviorProcessRequest(BaseModel):
    """Request trích đặc trưng cho một frame."""

    camera_id: int
    frame_id: int
    timestamp: Optional[str] = None
    tracks: List[TrackIn] = Field(default_factory=list)
    objects: List[DetectionObjectIn] = Field(default_factory=list)
    frame: Optional[str] = Field(
        default=None, description="Ảnh base64 (tùy chọn) để chạy pose"
    )


class BenchmarkRequest(BaseModel):
    """Request benchmark Behavior Engine."""

    frames: int = Field(default=120, ge=1, le=5000)
    people: int = Field(default=20, ge=1, le=200)
    width: int = Field(default=1280, ge=64, le=7680)
    height: int = Field(default=720, ge=64, le=4320)
    use_real_pose: bool = False
