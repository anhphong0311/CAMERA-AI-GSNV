"""
Unit test — TemporalBuffer & HistoryManager (300-frame buffer, prune, LRU).
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.behavior.history import (
    FrameSnapshot,
    HistoryManager,
    TemporalBuffer,
)


def _snapshot(center=(0.0, 0.0), speed=1.0, head_angle=10.0, wrist=(1.0, 1.0)):
    return FrameSnapshot(
        timestamp=datetime.now(timezone.utc),
        center=center,
        speed_px=speed,
        pose_present=True,
        head_angle=head_angle,
        head_direction="FORWARD",
        left_wrist=wrist,
        right_wrist=None,
        sitting=True,
        phone_near=False,
    )


def test_buffer_respects_capacity():
    buf = TemporalBuffer(buffer_size=5)
    for i in range(10):
        buf.append(_snapshot(center=(float(i), 0.0)), frame_id=i)
    assert buf.size == 5
    assert buf.centers()[-1] == (9.0, 0.0)  # giữ mới nhất


def test_buffer_prev_wrists_and_streak():
    buf = TemporalBuffer(10)
    s = _snapshot(wrist=(5.0, 5.0))
    buf.append(s, 0)
    assert buf.prev_wrists()[0] == (5.0, 5.0)


def test_phone_near_streak():
    buf = TemporalBuffer(10)
    for i in range(3):
        s = _snapshot()
        s.phone_near = True
        buf.append(s, i)
    assert buf.phone_near_streak() == 3


def test_history_manager_update_and_get():
    hm = HistoryManager(buffer_size=300, max_tracks=100)
    hm.update(1, _snapshot(), frame_id=0)
    assert hm.get(1) is not None
    assert hm.track_count == 1


def test_history_manager_prune_stale():
    hm = HistoryManager(buffer_size=10, max_tracks=100)
    hm.update(1, _snapshot(), frame_id=0)
    removed = hm.prune(current_frame_id=50)  # 50 - 0 > 10
    assert removed == 1
    assert hm.track_count == 0


def test_history_manager_lru_eviction():
    hm = HistoryManager(buffer_size=10, max_tracks=2)
    hm.update(1, _snapshot(), frame_id=0)
    hm.update(2, _snapshot(), frame_id=1)
    hm.update(3, _snapshot(), frame_id=2)  # vượt max_tracks → loại LRU (track 1)
    assert hm.track_count == 2
    assert hm.get(1) is None
    assert hm.get(3) is not None
