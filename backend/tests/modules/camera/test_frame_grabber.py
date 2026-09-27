"""Regression tests for low-latency RTSP frame sampling."""

from unittest.mock import Mock, patch

import numpy as np

from app.modules.camera.frame_buffer.buffer import FrameBuffer
from app.modules.camera.stream_worker.grabber import FrameGrabber


def test_grabber_drains_source_without_buffering_old_frames() -> None:
    client = Mock()
    client.read_frame.return_value = (np.zeros((8, 8, 3), dtype=np.uint8), 1.0, 1.0)
    buffer = FrameBuffer(max_size=2)
    grabber = FrameGrabber(
        camera_id=1,
        rtsp_client=client,
        frame_buffer=buffer,
        fps_monitor=Mock(),
        health_monitor=Mock(),
        target_fps=2,
    )

    # All three source frames are read. Only the first and the newest frame
    # after the 500 ms sampling interval are published.
    with patch(
        "app.modules.camera.stream_worker.grabber.time.monotonic",
        side_effect=[1.0, 1.1, 1.6],
    ):
        assert grabber.grab_once()
        assert grabber.grab_once()
        assert grabber.grab_once()

    assert client.read_frame.call_count == 3
    assert grabber.frame_id == 2
    assert buffer.latest() is not None
    assert buffer.latest().frame_id == 2
