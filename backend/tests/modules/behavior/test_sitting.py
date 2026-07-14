"""
Unit test — SittingFeatureExtractor (ngồi/đứng).
"""

from __future__ import annotations

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.sitting import SittingFeatureExtractor
from tests.modules.behavior.conftest import make_keypoints


def _extractor() -> SittingFeatureExtractor:
    return SittingFeatureExtractor(ThresholdConfig())


def test_standing_when_legs_extended():
    posture, sitting = _extractor().extract(make_keypoints())
    assert posture == "STANDING"
    assert sitting is False


def test_sitting_when_legs_occluded():
    # thiếu gối + cổ chân → coi là ngồi sau bàn
    kp = make_keypoints(missing=[13, 14, 15, 16])
    posture, sitting = _extractor().extract(kp)
    assert posture == "SITTING"
    assert sitting is True


def test_sitting_when_legs_folded():
    # cổ chân gần hông (chân co) → ngồi
    kp = make_keypoints(overrides={15: (120, 330), 16: (160, 330)})
    posture, sitting = _extractor().extract(kp)
    assert posture == "SITTING"


def test_unknown_when_no_hips():
    posture, sitting = _extractor().extract(make_keypoints(missing=[11, 12]))
    assert posture == "UNKNOWN"
