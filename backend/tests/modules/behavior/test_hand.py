"""
Unit test — HandFeatureExtractor (near-face/movement/speed).
"""

from __future__ import annotations

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.hand import HandFeatureExtractor
from tests.modules.behavior.conftest import make_keypoints

BBOX = (100.0, 140.0, 180.0, 520.0)


def _extractor() -> HandFeatureExtractor:
    return HandFeatureExtractor(ThresholdConfig())


def test_hand_positions_available():
    f = _extractor().extract(make_keypoints(), BBOX)
    assert f.available
    assert f.left_position is not None
    assert f.right_position is not None


def test_hand_not_near_face_by_default():
    f = _extractor().extract(make_keypoints(), BBOX)
    assert f.near_face is False


def test_hand_near_face():
    kp = make_keypoints(overrides={9: (140, 158)})  # cổ tay trái sát mũi
    f = _extractor().extract(kp, BBOX)
    assert f.near_face is True


def test_hand_movement_and_speed():
    kp = make_keypoints(overrides={9: (95, 300)})
    f = _extractor().extract(kp, BBOX, prev_left=(75, 300), prev_right=(185, 300))
    assert f.movement == 20.0
    assert f.speed == 20.0


def test_hand_missing_returns_unavailable():
    kp = make_keypoints(missing=[9, 10])
    f = _extractor().extract(kp, BBOX)
    assert not f.available
