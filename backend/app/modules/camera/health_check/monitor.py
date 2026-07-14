"""
Health Monitor — tổng hợp trạng thái camera runtime.
"""

import threading
from datetime import datetime
from typing import Optional

from app.modules.camera.fps_monitor.monitor import FPSMonitor
from app.modules.camera.frame_buffer.buffer import FrameBuffer
from app.modules.camera.models.frame import CameraRuntimeStatus, utc_now


class HealthMonitor:
    """
    Theo dõi online/offline, reconnect, dropped frames, FPS, latency.

    Cập nhật từ CameraWorker sau mỗi frame hoặc sự kiện lỗi.
    """

    def __init__(self, camera_id: int) -> None:
        self.camera_id = camera_id
        self._lock = threading.RLock()
        self._is_connected = False
        self._is_running = False
        self._reconnect_count = 0
        self._dropped_frames = 0
        self._last_frame_at: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._latency_ms = 0.0

    def set_running(self, running: bool) -> None:
        """Đánh dấu worker đang chạy hay đã dừng."""
        with self._lock:
            self._is_running = running

    def on_connected(self) -> None:
        """Gọi khi RTSP connect thành công."""
        with self._lock:
            self._is_connected = True
            self._last_error = None

    def on_disconnected(self, error: str | None = None) -> None:
        """Gọi khi mất kết nối RTSP."""
        with self._lock:
            self._is_connected = False
            if error:
                self._last_error = error

    def on_reconnect(self) -> None:
        """Tăng reconnect counter."""
        with self._lock:
            self._reconnect_count += 1

    def on_frame(
        self,
        fps_monitor: FPSMonitor,
        frame_buffer: FrameBuffer,
        read_time_ms: float,
    ) -> None:
        """
        Cập nhật metrics sau mỗi frame đọc thành công.

        Args:
            fps_monitor: FPSMonitor của worker.
            frame_buffer: Buffer để lấy queue size và dropped count.
            read_time_ms: Latency đọc frame.
        """
        with self._lock:
            self._last_frame_at = utc_now()
            self._latency_ms = read_time_ms
            self._dropped_frames = frame_buffer.dropped_count

    def get_status(
        self,
        fps_monitor: FPSMonitor,
        frame_buffer: FrameBuffer,
    ) -> CameraRuntimeStatus:
        """
        Tổng hợp CameraRuntimeStatus cho API.

        Args:
            fps_monitor: Nguồn FPS metrics.
            frame_buffer: Nguồn queue size.

        Returns:
            CameraRuntimeStatus: Snapshot trạng thái hiện tại.
        """
        with self._lock:
            if self._is_running and self._is_connected:
                status = "online"
            elif self._is_running:
                status = "reconnecting"
            else:
                status = "offline"

            return CameraRuntimeStatus(
                camera_id=self.camera_id,
                is_running=self._is_running,
                is_connected=self._is_connected,
                status=status,
                reconnect_count=self._reconnect_count,
                dropped_frames=self._dropped_frames,
                current_fps=fps_monitor.current_fps,
                average_fps=fps_monitor.average_fps,
                latency_ms=self._latency_ms,
                queue_size=frame_buffer.size,
                last_frame_at=self._last_frame_at,
                last_error=self._last_error,
            )
