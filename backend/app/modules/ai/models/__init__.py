"""Domain DTO models — AI Detection Engine (in-memory, không phải ORM)."""

from app.modules.ai.models.benchmark import BenchmarkResult
from app.modules.ai.models.detection import (
    BoundingBox,
    Detection,
    DetectionResult,
    utc_now,
)
from app.modules.ai.models.model_info import ModelInfo
from app.modules.ai.models.raw import RawDetection

__all__ = [
    "BenchmarkResult",
    "BoundingBox",
    "Detection",
    "DetectionResult",
    "ModelInfo",
    "RawDetection",
    "utc_now",
]
