"""
Unit test — Keypoints DTO và geometry utils.
"""

from __future__ import annotations

import math

from app.modules.behavior.models.keypoints import NOSE, Keypoints
from app.modules.behavior.utils.geometry import (
    bbox_iou,
    distance,
    midpoint,
    scale_from,
)
from tests.modules.behavior.conftest import make_keypoints


def test_keypoint_get_respects_confidence():
    kp = Keypoints([(10.0, 20.0, 0.9), (0.0, 0.0, 0.1)], min_conf=0.3)
    assert kp.get(0) == (10.0, 20.0)
    assert kp.get(1) is None  # dưới ngưỡng
    assert kp.get(99) is None


def test_keypoint_valid_count():
    kp = make_keypoints(missing=[NOSE])
    assert kp.valid_count() == 16


def test_geometry_distance_and_midpoint():
    assert distance((0.0, 0.0), (3.0, 4.0)) == 5.0
    assert distance(None, (1.0, 1.0)) is None
    assert midpoint((0.0, 0.0), (2.0, 4.0)) == (1.0, 2.0)


def test_bbox_iou():
    a = (0.0, 0.0, 10.0, 10.0)
    b = (0.0, 0.0, 10.0, 10.0)
    assert bbox_iou(a, b) == 1.0
    c = (20.0, 20.0, 30.0, 30.0)
    assert bbox_iou(a, c) == 0.0


def test_scale_from_uses_shoulder_width():
    s = scale_from((100.0, 200.0), (180.0, 200.0), (0, 0, 200, 400))
    assert math.isclose(s, 80.0)


def test_scale_from_fallback_bbox():
    s = scale_from(None, None, (0.0, 0.0, 100.0, 200.0))
    assert s > 0
