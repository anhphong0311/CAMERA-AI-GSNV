"""
Fixtures dùng chung cho test Tracking Engine.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.modules.ai.models import BoundingBox, Detection, DetectionResult, utc_now
from app.modules.tracking.config import (
    LifecycleConfig,
    MotionConfig,
    ROIRegionConfig,
    TrackerConfig,
    TrackingConfig,
)


@pytest.fixture
def tracking_config() -> TrackingConfig:
    """TrackingConfig mặc định cho test."""
    return TrackingConfig(
        tracker=TrackerConfig(
            track_thresh=0.5,
            new_track_thresh=0.6,
            match_thresh=0.8,
            track_buffer=30,
            min_box_area=50.0,
            frame_rate=30,
        ),
        lifecycle=LifecycleConfig(max_lost_frames=30, max_tracks=300),
        motion=MotionConfig(history_size=60, stationary_speed=2.0),
    )


@pytest.fixture
def sample_roi_config() -> ROIRegionConfig:
    """Một ROI hình chữ nhật góc trái trên (0..320, 0..240)."""
    return ROIRegionConfig(
        id="desk_01",
        name="Desk 01",
        polygon=[[0, 0], [320, 0], [320, 240], [0, 240]],
        color="#22c55e",
        description="Bàn 01",
    )


def make_detection_result(
    camera_id: int,
    frame_id: int,
    boxes: list[tuple[float, float, float, float]],
    base_time=None,
    width: int = 1280,
    height: int = 720,
    class_name: str = "person",
) -> DetectionResult:
    """Tạo DetectionResult giả từ danh sách bbox."""
    ts = (base_time or utc_now()) + timedelta(seconds=frame_id / 30.0)
    objects = [
        Detection(class_name=class_name, confidence=0.9, bbox=BoundingBox(*b), class_id=0)
        for b in boxes
    ]
    return DetectionResult(
        camera_id=camera_id,
        frame_id=frame_id,
        timestamp=ts,
        objects=objects,
        width=width,
        height=height,
    )
