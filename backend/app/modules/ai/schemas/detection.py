"""
Pydantic schemas — AI Detection API request/response.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    """Body POST /ai/inference — ảnh base64."""

    image_base64: str = Field(..., description="Ảnh JPEG/PNG mã hóa base64")
    camera_id: int = Field(default=0, description="ID camera nguồn (metadata)")
    frame_id: int = Field(default=0, description="Số thứ tự frame")
    visualize: bool = Field(
        default=False, description="Trả kèm ảnh overlay bbox (base64) để debug"
    )


class DetectionObjectSchema(BaseModel):
    """Một object trong kết quả (mô tả OpenAPI)."""

    class_name: str = Field(..., alias="class")
    class_id: int
    confidence: float
    bbox: dict[str, float]
    center: dict[str, float]
    width: float
    height: float

    model_config = {"populate_by_name": True}


class DetectionResultSchema(BaseModel):
    """Response DetectionResult chuẩn."""

    camera_id: int
    frame_id: int
    timestamp: str
    objects: List[dict[str, Any]]
    count: int
    inference_time_ms: float
    model_name: str
    fps: float
    width: int
    height: int
    overlay_base64: Optional[str] = Field(
        default=None, description="Ảnh overlay debug (chỉ khi visualize=true)"
    )


class ReloadRequest(BaseModel):
    """Body POST /ai/reload (tùy chọn — Sprint 3 dùng config hiện tại)."""

    warmup: bool = Field(default=True, description="Warmup sau khi reload")


class BenchmarkRequest(BaseModel):
    """Body POST /ai/benchmark."""

    runs: int = Field(default=50, ge=1, le=1000)
    image_size: Optional[int] = Field(default=None, ge=32, le=4096)
    warmup: int = Field(default=5, ge=0, le=100)


class ModelInfoSchema(BaseModel):
    """Response GET /ai/model."""

    name: str
    path: str
    device: str
    image_size: int
    half_precision: bool
    loaded: bool
    warmup_done: bool
    loaded_at: Optional[str] = None
    class_labels: List[str]
