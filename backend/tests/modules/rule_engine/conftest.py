"""
Fixtures + builders cho test Rule Engine (Sprint 6).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import pytest

from app.modules.behavior.models import (
    BehaviorFeatureDTO,
    BehaviorResult,
    TrackingView,
    TrackView,
)
from app.modules.rule_engine.config import (
    CooldownConfig,
    RuleEngineConfig,
)
from app.modules.rule_engine.services import RuleService

BASE_TIME = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)


def make_dto(
    track_id: int,
    *,
    ts: Optional[datetime] = None,
    phone_visible: bool = False,
    hand_near_phone: bool = False,
    looking: str = "FORWARD",
    head_direction: str = "FORWARD",
    head_stability: float = 1.0,
    movement_speed: float = 0.0,
    motion_direction: str = "STATIONARY",
    stationary_time: float = 0.0,
    sitting: bool = True,
    hand_on_desk: bool = False,
    hand_near_face: bool = False,
    body_in_roi: bool = True,
    food_mouth: Optional[float] = None,
    cup_mouth: Optional[float] = None,
    bottle_mouth: Optional[float] = None,
    food_near_mouth: bool = False,
) -> BehaviorFeatureDTO:
    """Tạo BehaviorFeatureDTO với các cờ điều khiển facts."""
    dto = BehaviorFeatureDTO(track_id=track_id, timestamp=ts or BASE_TIME)
    dto.head.direction = head_direction
    dto.head.stability = head_stability
    dto.head.available = True
    dto.gaze.looking = looking
    dto.gaze.confidence = 0.8
    dto.motion.movement_speed = movement_speed
    dto.motion.direction = motion_direction
    dto.motion.stationary_time = stationary_time
    dto.hand.near_phone = hand_near_phone
    dto.hand.near_face = hand_near_face
    dto.hand.available = True
    dto.phone_feature.visible = phone_visible
    dto.chair_feature.sitting = sitting
    dto.chair_feature.hand_on_desk = hand_on_desk
    dto.chair_feature.body_in_roi = body_in_roi
    dto.food_feature.food_mouth = food_mouth
    dto.food_feature.cup_mouth = cup_mouth
    dto.food_feature.bottle_mouth = bottle_mouth
    dto.food_feature.near_mouth = food_near_mouth
    return dto


def make_behavior_result(
    camera_id: int,
    frame_id: int,
    features: List[BehaviorFeatureDTO],
    ts: Optional[datetime] = None,
) -> BehaviorResult:
    """Tạo BehaviorResult cho một frame."""
    return BehaviorResult(
        camera_id=camera_id,
        frame_id=frame_id,
        timestamp=ts or BASE_TIME,
        features=features,
    )


def make_tracking(
    camera_id: int,
    frame_id: int,
    tracks: List[Tuple[int, Tuple[float, float, float, float], Optional[str]]],
    ts: Optional[datetime] = None,
) -> TrackingView:
    """Tạo TrackingView từ (track_id, bbox, roi)."""
    views = [
        TrackView(
            track_id=tid,
            camera_id=camera_id,
            bbox=bbox,
            current_roi_id=roi,
        )
        for tid, bbox, roi in tracks
    ]
    return TrackingView(
        camera_id=camera_id,
        frame_id=frame_id,
        timestamp=ts or BASE_TIME,
        tracks=views,
    )


def at(seconds: float) -> datetime:
    """Mốc thời gian tương đối BASE_TIME."""
    return BASE_TIME + timedelta(seconds=seconds)


@pytest.fixture
def engine_config() -> RuleEngineConfig:
    """Config engine mặc định."""
    return RuleEngineConfig()


@pytest.fixture
def cooldown_config() -> CooldownConfig:
    """Config cooldown mặc định."""
    return CooldownConfig()


@pytest.fixture
def service() -> RuleService:
    """RuleService đã seed rules từ rules.yaml."""
    svc = RuleService()
    svc.load_rules_file()
    return svc
