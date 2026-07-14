"""
Unit test — BehaviorFeatureEngine (orchestrator trích đặc trưng).
"""

from __future__ import annotations

from app.modules.ai.models import BoundingBox, Detection
from app.modules.behavior.config import BehaviorConfig
from app.modules.behavior.feature_engine import BehaviorFeatureEngine
from tests.modules.behavior.conftest import make_pose, make_tracking_view

TRACK_BBOX = (100.0, 140.0, 180.0, 360.0)


def _detections():
    return [
        Detection("phone", 0.9, BoundingBox(115, 257, 135, 277), 67),
        Detection("monitor", 0.9, BoundingBox(300, 140, 360, 300), 62),
        Detection("chair", 0.9, BoundingBox(100, 300, 180, 360), 56),
    ]


def test_engine_extracts_full_feature():
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    tv = make_tracking_view(1, 0, [(7, TRACK_BBOX)], speed_px=1.0)
    poses = [make_pose(TRACK_BBOX)]
    result = engine.process(tv, poses, _detections())

    assert result.count == 1
    dto = result.features[0]
    assert dto.track_id == 7
    assert dto.head.available
    assert dto.body.available
    assert dto.hand.available


def test_engine_phone_and_gaze():
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    tv = make_tracking_view(1, 0, [(7, TRACK_BBOX)])
    dto = engine.process(tv, [make_pose(TRACK_BBOX)], _detections()).features[0]
    assert dto.phone_feature.visible is True
    assert dto.hand.near_phone is True
    assert dto.gaze.looking == "MONITOR"


def test_engine_ignores_desk_phone():
    """Điện thoại trên bàn (súng quét mã) không được tính là phone của người."""
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    tv = make_tracking_view(1, 0, [(7, TRACK_BBOX)])
    dets = _detections() + [
        Detection("phone", 0.85, BoundingBox(40, 340, 90, 380), 67),
    ]
    dto = engine.process(tv, [make_pose(TRACK_BBOX)], dets).features[0]
    assert dto.phone_feature.visible is True
    assert dto.hand.near_phone is True


def test_engine_chair_detected():
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    tv = make_tracking_view(1, 0, [(7, TRACK_BBOX)])
    dto = engine.process(tv, [make_pose(TRACK_BBOX)], _detections()).features[0]
    assert dto.chair_feature.chair_detected is True


def test_engine_without_pose_motion_only():
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    tv = make_tracking_view(1, 0, [(7, TRACK_BBOX)], speed_px=4.0, direction="RIGHT")
    dto = engine.process(tv, [], None).features[0]
    assert dto.head.available is False
    assert dto.motion.movement_speed == 4.0


def test_engine_temporal_grows():
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    for f in range(5):
        tv = make_tracking_view(1, f, [(7, TRACK_BBOX)])
        engine.process(tv, [make_pose(TRACK_BBOX)], _detections())
    buf = engine.history.get(7)
    assert buf is not None
    assert buf.size == 5


def test_engine_handles_20_people():
    engine = BehaviorFeatureEngine(1, BehaviorConfig())
    tracks = []
    poses = []
    for i in range(20):
        bx = 20 + (i % 10) * 120
        by = 40 + (i // 10) * 260
        bbox = (float(bx), float(by), float(bx + 80), float(by + 220))
        tracks.append((i + 1, bbox))
        poses.append(make_pose(bbox))
    tv = make_tracking_view(1, 0, tracks)
    result = engine.process(tv, poses, None)
    assert result.count == 20
