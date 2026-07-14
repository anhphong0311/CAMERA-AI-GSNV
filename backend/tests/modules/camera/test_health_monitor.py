"""
Unit tests — HealthMonitor metrics aggregation.
"""

import numpy as np
import pytest

from app.modules.camera.frame_buffer.buffer import FrameBuffer
from app.modules.camera.fps_monitor.monitor import FPSMonitor
from app.modules.camera.health_check.monitor import HealthMonitor
from app.modules.camera.models.frame import FramePacket, utc_now


class TestHealthMonitor:
    """Test HealthMonitor."""

    def test_online_status_when_connected(self) -> None:
        """Connected + running → status online."""
        health = HealthMonitor(camera_id=1)
        fps = FPSMonitor()
        buf = FrameBuffer(max_size=5)
        health.set_running(True)
        health.on_connected()
        fps.record_frame(10.0, 10.0)
        health.on_frame(fps, buf, 10.0)
        status = health.get_status(fps, buf)
        assert status.status == "online"
        assert status.is_connected is True

    def test_reconnecting_when_running_not_connected(self) -> None:
        """Running nhưng disconnected → reconnecting."""
        health = HealthMonitor(camera_id=1)
        health.set_running(True)
        health.on_disconnected("test error")
        status = health.get_status(FPSMonitor(), FrameBuffer())
        assert status.status == "reconnecting"
        assert status.last_error == "test error"

    def test_reconnect_count_increments(self) -> None:
        """on_reconnect tăng counter."""
        health = HealthMonitor(camera_id=1)
        health.on_reconnect()
        health.on_reconnect()
        status = health.get_status(FPSMonitor(), FrameBuffer())
        assert status.reconnect_count == 2

    def test_dropped_frames_from_buffer(self) -> None:
        """Dropped frames lấy từ FrameBuffer."""
        health = HealthMonitor(camera_id=1)
        buf = FrameBuffer(max_size=1)
        buf.push(
            FramePacket(
                camera_id=1,
                frame_id=1,
                timestamp=utc_now(),
                data=np.zeros((10, 10, 3), dtype=np.uint8),
            )
        )
        buf.push(
            FramePacket(
                camera_id=1,
                frame_id=2,
                timestamp=utc_now(),
                data=np.zeros((10, 10, 3), dtype=np.uint8),
            )
        )
        health.on_frame(FPSMonitor(), buf, 5.0)
        status = health.get_status(FPSMonitor(), buf)
        assert status.dropped_frames >= 1
