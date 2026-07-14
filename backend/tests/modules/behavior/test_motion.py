"""
Unit test — MotionFeatureExtractor (stationary time, distance, direction).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.behavior.motion import MotionFeatureExtractor


def _timestamps(n: int):
    base = datetime.now(timezone.utc)
    return [base + timedelta(seconds=i / 30.0) for i in range(n)]


def test_movement_distance_sum():
    ext = MotionFeatureExtractor(frame_rate=30, stationary_speed=2.0)
    centers = [(0.0, 0.0), (3.0, 4.0), (6.0, 8.0)]
    f = ext.extract(5.0, "RIGHT", centers, _timestamps(3), [5.0, 5.0, 5.0])
    assert f.movement_distance == 10.0
    assert f.movement_speed == 5.0
    assert f.direction == "RIGHT"


def test_stationary_time_accumulates():
    ext = MotionFeatureExtractor(frame_rate=30, stationary_speed=2.0)
    ts = _timestamps(10)
    centers = [(0.0, 0.0)] * 10
    speeds = [0.5] * 10  # đều dưới ngưỡng
    f = ext.extract(0.5, "STATIONARY", centers, ts, speeds)
    # 9 khoảng * (1/30) giây
    assert f.stationary_time > 0.29
    assert f.direction == "STATIONARY"


def test_moving_resets_stationary():
    ext = MotionFeatureExtractor(frame_rate=30, stationary_speed=2.0)
    ts = _timestamps(5)
    centers = [(0.0, 0.0)] * 5
    speeds = [0.1, 0.1, 0.1, 0.1, 10.0]  # frame cuối di chuyển
    f = ext.extract(10.0, "LEFT", centers, ts, speeds)
    assert f.stationary_time == 0.0
