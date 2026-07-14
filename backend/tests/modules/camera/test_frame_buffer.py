"""
Unit tests — FrameBuffer thread-safe queue.
"""

import threading

import numpy as np
import pytest

from app.modules.camera.frame_buffer.buffer import FrameBuffer
from app.modules.camera.models.frame import FramePacket, utc_now


def _make_frame(camera_id: int = 1, frame_id: int = 1) -> FramePacket:
    """Helper tạo FramePacket giả."""
    return FramePacket(
        camera_id=camera_id,
        frame_id=frame_id,
        timestamp=utc_now(),
        data=np.zeros((480, 640, 3), dtype=np.uint8),
    )


class TestFrameBuffer:
    """Test suite FrameBuffer."""

    def test_push_pop_fifo(self) -> None:
        """Push 3 frame — pop trả FIFO."""
        buf = FrameBuffer(max_size=10)
        f1, f2 = _make_frame(frame_id=1), _make_frame(frame_id=2)
        buf.push(f1)
        buf.push(f2)
        assert buf.pop().frame_id == 1
        assert buf.pop().frame_id == 2

    def test_latest_returns_newest(self) -> None:
        """latest() trả frame mới nhất không xóa."""
        buf = FrameBuffer(max_size=10)
        buf.push(_make_frame(frame_id=1))
        buf.push(_make_frame(frame_id=2))
        latest = buf.latest()
        assert latest is not None
        assert latest.frame_id == 2
        assert buf.size == 2

    def test_drop_old_when_full(self) -> None:
        """Queue đầy — dropped_count tăng."""
        buf = FrameBuffer(max_size=2)
        buf.push(_make_frame(frame_id=1))
        buf.push(_make_frame(frame_id=2))
        buf.push(_make_frame(frame_id=3))
        assert buf.dropped_count >= 1
        assert buf.latest().frame_id == 3

    def test_clear(self) -> None:
        """clear() xóa hết buffer."""
        buf = FrameBuffer(max_size=5)
        buf.push(_make_frame())
        buf.clear()
        assert buf.size == 0
        assert buf.latest() is None

    def test_thread_safe_concurrent_push(self) -> None:
        """100 thread push đồng thời — không crash."""
        buf = FrameBuffer(max_size=50)
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                for j in range(20):
                    buf.push(_make_frame(frame_id=i * 100 + j))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert buf.latest() is not None
