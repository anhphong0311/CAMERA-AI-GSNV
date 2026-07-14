"""Schemas package — Tracking Engine."""

from app.modules.tracking.schemas.tracking import (
    BenchmarkRequest,
    DetectionObjectIn,
    DetectionResultRequest,
)

__all__ = ["BenchmarkRequest", "DetectionObjectIn", "DetectionResultRequest"]
