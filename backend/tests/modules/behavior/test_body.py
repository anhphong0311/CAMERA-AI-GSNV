"""
Unit test — BodyFeatureExtractor (lean/angle).
"""

from __future__ import annotations

from app.modules.behavior.body import BodyFeatureExtractor
from app.modules.behavior.config import ThresholdConfig
from tests.modules.behavior.conftest import make_keypoints

BBOX = (100.0, 140.0, 180.0, 520.0)


def _extractor() -> BodyFeatureExtractor:
    return BodyFeatureExtractor(ThresholdConfig())


def test_body_neutral():
    f = _extractor().extract(make_keypoints(), BBOX)
    assert f.available
    assert f.lean == "NEUTRAL"


def test_body_lean_forward():
    # vai lệch phải so với hông → FORWARD
    kp = make_keypoints(overrides={5: (140, 200), 6: (220, 200)})
    f = _extractor().extract(kp, BBOX)
    assert f.lean == "FORWARD"


def test_body_lean_back():
    kp = make_keypoints(overrides={5: (60, 200), 6: (140, 200)})
    f = _extractor().extract(kp, BBOX)
    assert f.lean == "BACK"


def test_body_missing_hips_unavailable():
    kp = make_keypoints(missing=[11, 12])
    f = _extractor().extract(kp, BBOX)
    assert not f.available
