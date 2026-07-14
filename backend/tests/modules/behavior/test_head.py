"""
Unit test — HeadFeatureExtractor (direction/angle/stability).
"""

from __future__ import annotations

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.head import HeadFeatureExtractor
from tests.modules.behavior.conftest import make_keypoints

BBOX = (100.0, 140.0, 180.0, 520.0)


def _extractor() -> HeadFeatureExtractor:
    return HeadFeatureExtractor(ThresholdConfig())


def test_head_forward():
    kp = make_keypoints()  # nhìn thẳng
    f = _extractor().extract(kp, BBOX)
    assert f.available
    assert f.direction == "FORWARD"


def test_head_down():
    kp = make_keypoints(overrides={0: (140, 185)})  # mũi dưới tai
    f = _extractor().extract(kp, BBOX)
    assert f.direction == "DOWN"
    assert f.angle > 20


def test_head_up():
    kp = make_keypoints(overrides={0: (140, 135)})
    f = _extractor().extract(kp, BBOX)
    assert f.direction == "UP"


def test_head_left():
    kp = make_keypoints(overrides={0: (118, 150)})
    f = _extractor().extract(kp, BBOX)
    assert f.direction == "LEFT"


def test_head_right():
    kp = make_keypoints(overrides={0: (162, 150)})
    f = _extractor().extract(kp, BBOX)
    assert f.direction == "RIGHT"


def test_head_missing_returns_unavailable():
    kp = make_keypoints(missing=[0, 5, 6])  # thiếu mũi + vai
    f = _extractor().extract(kp, BBOX)
    assert not f.available


def test_head_stability_high_when_stable():
    f = _extractor().extract(make_keypoints(), BBOX, recent_angles=[10, 10.2, 9.9])
    assert f.stability > 0.9


def test_head_stability_low_when_jittery():
    f = _extractor().extract(make_keypoints(), BBOX, recent_angles=[0, 60, -40, 50])
    assert f.stability < 0.5
