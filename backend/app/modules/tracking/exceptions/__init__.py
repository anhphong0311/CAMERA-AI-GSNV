"""Exceptions package — Tracking Engine."""

from app.modules.tracking.exceptions.errors import (
    InvalidDetectionError,
    MemoryOverflowError,
    ROIError,
    TrackingException,
    TrackingLostError,
    TrackOverflowError,
)

__all__ = [
    "InvalidDetectionError",
    "MemoryOverflowError",
    "ROIError",
    "TrackOverflowError",
    "TrackingException",
    "TrackingLostError",
]
