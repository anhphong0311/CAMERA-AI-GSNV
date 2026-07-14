"""
Pydantic schemas — Tracking API request/response.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DetectionObjectIn(BaseModel):
    """Một object detection đầu vào (đến từ Detection Engine)."""

    class_name: str = Field(default="person", alias="class")
    class_id: int = 0
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] pixel gốc")

    model_config = {"populate_by_name": True}


class DetectionResultRequest(BaseModel):
    """
    Body POST /tracking/process — một DetectionResult để chạy tracking.

    Cho phép feed thủ công (integration/test) mà không cần pipeline đầy đủ.
    """

    camera_id: int
    frame_id: int = 0
    timestamp: Optional[str] = Field(
        default=None, description="ISO datetime; mặc định thời điểm hiện tại"
    )
    width: int = 0
    height: int = 0
    objects: List[DetectionObjectIn] = Field(default_factory=list)


class BenchmarkRequest(BaseModel):
    """Body POST /tracking/benchmark."""

    frames: int = Field(default=100, ge=1, le=5000)
    num_people: int = Field(default=20, ge=1, le=200)
    width: int = Field(default=1280, ge=64, le=7680)
    height: int = Field(default=720, ge=64, le=4320)
