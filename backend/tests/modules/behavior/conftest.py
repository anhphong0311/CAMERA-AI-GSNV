"""
Fixtures dùng chung cho test Behavior Feature Engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import pytest

from app.modules.behavior.config import BehaviorConfig
from app.modules.behavior.models import (
    Keypoints,
    PoseResult,
    TrackingView,
    TrackView,
)
from app.modules.behavior.models.keypoints import (
    LEFT_ANKLE,
    LEFT_EAR,
    LEFT_EYE,
    LEFT_HIP,
    LEFT_KNEE,
    LEFT_SHOULDER,
    LEFT_WRIST,
    NOSE,
    RIGHT_ANKLE,
    RIGHT_EAR,
    RIGHT_EYE,
    RIGHT_HIP,
    RIGHT_KNEE,
    RIGHT_SHOULDER,
    RIGHT_WRIST,
)

Point = Tuple[float, float]


@pytest.fixture
def behavior_config() -> BehaviorConfig:
    """Config behavior mặc định cho test (dùng giá trị default)."""
    return BehaviorConfig()


def make_keypoints(
    overrides: Optional[dict[int, Point]] = None,
    missing: Optional[list[int]] = None,
    min_conf: float = 0.3,
) -> Keypoints:
    """
    Tạo skeleton COCO-17 mặc định (đứng, nhìn thẳng); cho phép override joint.

    Args:
        overrides: dict index → (x, y) để chỉnh.
        missing: danh sách index đặt confidence = 0 (thiếu joint).
    """
    # Mặc định: vai y=200 rộng 80, mũi trên neck, hông/gối/cổ chân bên dưới
    default: dict[int, Point] = {
        NOSE: (140, 150),
        LEFT_EYE: (130, 145),
        RIGHT_EYE: (150, 145),
        LEFT_EAR: (125, 146),
        RIGHT_EAR: (155, 146),
        LEFT_SHOULDER: (100, 200),
        RIGHT_SHOULDER: (180, 200),
        7: (95, 250),   # left_elbow
        8: (185, 250),  # right_elbow
        LEFT_WRIST: (95, 300),
        RIGHT_WRIST: (185, 300),
        LEFT_HIP: (120, 300),
        RIGHT_HIP: (160, 300),
        LEFT_KNEE: (120, 400),
        RIGHT_KNEE: (160, 400),
        LEFT_ANKLE: (120, 500),
        RIGHT_ANKLE: (160, 500),
    }
    if overrides:
        default.update(overrides)
    missing_set = set(missing or [])
    points: List[Tuple[float, float, float]] = []
    for i in range(17):
        x, y = default[i]
        conf = 0.0 if i in missing_set else 0.9
        points.append((float(x), float(y), conf))
    return Keypoints(points, min_conf)


def skeleton_for_bbox(bbox: Tuple[float, float, float, float]) -> Keypoints:
    """Skeleton hợp lý (đứng) bên trong bbox."""
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    cx = (x1 + x2) / 2.0

    def p(dx: float, dy: float) -> Tuple[float, float]:
        return (cx + dx * w, y1 + dy * h)

    overrides = {
        NOSE: p(0.0, 0.12),
        LEFT_EYE: p(-0.05, 0.10),
        RIGHT_EYE: p(0.05, 0.10),
        LEFT_EAR: p(-0.08, 0.11),
        RIGHT_EAR: p(0.08, 0.11),
        LEFT_SHOULDER: p(-0.18, 0.25),
        RIGHT_SHOULDER: p(0.18, 0.25),
        7: p(-0.20, 0.42),
        8: p(0.20, 0.42),
        LEFT_WRIST: p(-0.18, 0.58),
        RIGHT_WRIST: p(0.18, 0.58),
        LEFT_HIP: p(-0.12, 0.55),
        RIGHT_HIP: p(0.12, 0.55),
        LEFT_KNEE: p(-0.12, 0.78),
        RIGHT_KNEE: p(0.12, 0.78),
        LEFT_ANKLE: p(-0.12, 0.98),
        RIGHT_ANKLE: p(0.12, 0.98),
    }
    return make_keypoints(overrides)


def make_tracking_view(
    camera_id: int,
    frame_id: int,
    tracks: List[Tuple[int, Tuple[float, float, float, float]]],
    base_time: Optional[datetime] = None,
    speed_px: float = 0.0,
    direction: str = "STATIONARY",
) -> TrackingView:
    """Tạo TrackingView giả từ (track_id, bbox)."""
    ts = (base_time or datetime.now(timezone.utc)) + timedelta(
        seconds=frame_id / 30.0
    )
    views = [
        TrackView(
            track_id=tid,
            camera_id=camera_id,
            bbox=bbox,
            speed_px=speed_px,
            direction=direction,
        )
        for tid, bbox in tracks
    ]
    return TrackingView(
        camera_id=camera_id, frame_id=frame_id, timestamp=ts, tracks=views
    )


def make_pose(bbox: Tuple[float, float, float, float], score: float = 0.9) -> PoseResult:
    """PoseResult với skeleton hợp lý cho bbox."""
    return PoseResult(bbox=bbox, score=score, keypoints=skeleton_for_bbox(bbox))
