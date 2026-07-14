"""
FrameGrabber — đọc liên tục frame từ RTSPClient, đẩy vào FrameBuffer.

Chạy trong thread của CameraWorker — blocking I/O.
"""

import time
from typing import Callable, Optional

from loguru import logger

from app.modules.camera.frame_buffer.buffer import FrameBuffer
from app.modules.camera.fps_monitor.monitor import FPSMonitor
from app.modules.camera.health_check.monitor import HealthMonitor
from app.modules.camera.models.frame import FramePacket, utc_now
from app.modules.camera.stream_reader.rtsp_client import RTSPClient


class FrameGrabber:
    """
    Liên tục đọc frame từ RTSP và push vào buffer.

    Không làm AI — chỉ capture frame thô.
    """

    def __init__(
        self,
        camera_id: int,
        rtsp_client: RTSPClient,
        frame_buffer: FrameBuffer,
        fps_monitor: FPSMonitor,
        health_monitor: HealthMonitor,
        target_fps: int = 15,
        on_frame: Optional[Callable] = None,
    ) -> None:
        self.camera_id = camera_id
        self._client = rtsp_client
        self._buffer = frame_buffer
        self._fps = fps_monitor
        self._health = health_monitor
        self._target_fps = target_fps
        self._frame_id = 0
        self._min_interval = 1.0 / target_fps if target_fps > 0 else 0
        self._on_frame = on_frame

    def set_frame_sink(self, sink: Optional[Callable]) -> None:
        self._on_frame = sink

    def grab_once(self) -> bool:
        """
        Đọc một frame và đẩy vào queue.

        Returns:
            bool: True nếu đọc thành công.
        """
        loop_start = time.monotonic()
        frame_data, read_ms, decode_ms = self._client.read_frame()

        if frame_data is None:
            return False

        self._frame_id += 1
        packet = FramePacket(
            camera_id=self.camera_id,
            frame_id=self._frame_id,
            timestamp=utc_now(),
            data=frame_data,
            read_time_ms=read_ms,
            decode_time_ms=decode_ms,
        )
        self._buffer.push(packet)
        if self._on_frame is not None:
            try:
                self._on_frame(self.camera_id, packet)
            except Exception as exc:
                logger.debug("Frame sink error cam={}: {}", self.camera_id, exc)
        self._fps.record_frame(read_ms, decode_ms)
        self._health.on_frame(self._fps, self._buffer, read_ms)

        # Giới hạn FPS mục tiêu — tránh đọc quá nhanh làm đầy CPU
        if self._min_interval > 0:
            elapsed = time.monotonic() - loop_start
            sleep_time = self._min_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        return True

    @property
    def frame_id(self) -> int:
        """Số frame cuối cùng đã đọc."""
        return self._frame_id
