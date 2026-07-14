"""Tracking engine package — orchestrator + tracker abstraction."""

from app.modules.tracking.tracking_engine.base_tracker import (
    BaseTracker,
    DetectionInput,
)
from app.modules.tracking.tracking_engine.engine import TrackingEngine
from app.modules.tracking.tracking_engine.factory import create_tracker

__all__ = ["BaseTracker", "DetectionInput", "TrackingEngine", "create_tracker"]
