"""Schemas package — Behavior API."""

from app.modules.behavior.schemas.behavior import (
    BehaviorProcessRequest,
    BenchmarkRequest,
    DetectionObjectIn,
    TrackIn,
)

__all__ = [
    "BehaviorProcessRequest",
    "BenchmarkRequest",
    "DetectionObjectIn",
    "TrackIn",
]
