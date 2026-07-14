"""Tests — Evidence Frame Buffer."""

from datetime import datetime, timedelta, timezone

import numpy as np

from app.modules.event.evidence.frame_buffer import EvidenceFrameBuffer


def _ts(sec: float) -> datetime:
    return datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=sec)


def test_frame_buffer_nearest_snapshot():
    buf = EvidenceFrameBuffer(seconds=30, fps=15)
    f1 = np.zeros((48, 64, 3), dtype=np.uint8)
    f2 = np.ones((48, 64, 3), dtype=np.uint8) * 255
    buf.push(f1, _ts(0), frame_index=1)
    buf.push(f2, _ts(2), frame_index=2)
    snap = buf.get_snapshot(_ts(2))
    assert snap is not None
    assert snap[0, 0, 0] == 255


def test_frame_buffer_video_window():
    buf = EvidenceFrameBuffer(seconds=30, fps=15)
    for i in range(5):
        f = np.full((10, 10, 3), i, dtype=np.uint8)
        buf.push(f, _ts(i))
    frames = buf.window(_ts(2), pre_seconds=1, post_seconds=1)
    assert len(frames) >= 2
