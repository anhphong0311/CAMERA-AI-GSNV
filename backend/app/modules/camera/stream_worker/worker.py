"""
CameraWorker — một thread riêng cho mỗi camera.

Chịu trách nhiệm: đọc frame, reconnect, monitor FPS/health.
"""

import threading
import time
from typing import Callable, Optional

from loguru import logger

from app.modules.camera.frame_buffer.buffer import FrameBuffer
from app.modules.camera.fps_monitor.monitor import FPSMonitor
from app.modules.camera.health_check.monitor import HealthMonitor
from app.modules.camera.models.frame import CameraRuntimeStatus
from app.modules.camera.reconnect.backoff import ReconnectPolicy
from app.modules.camera.stream_reader.rtsp_client import RTSPClient
from app.modules.camera.stream_worker.grabber import FrameGrabber
from app.modules.camera.utils.config_loader import CameraStreamConfig


class CameraWorker:
    """
    Worker độc lập cho một camera — chạy trong daemon thread.

    Một camera lỗi không ảnh hưởng worker khác (bulkhead).
    """

    def __init__(
        self,
        camera_id: int,
        rtsp_url: str,
        config: CameraStreamConfig,
        on_status_change: Optional[Callable[[CameraRuntimeStatus], None]] = None,
        on_frame: Optional[Callable] = None,
    ) -> None:
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.config = config
        self._on_status_change = on_status_change
        self._on_frame = on_frame

        self._buffer = FrameBuffer(
            max_size=max(config.queue_size, config.buffer_size),
            retention_seconds=30.0,
        )
        self._fps = FPSMonitor()
        self._health = HealthMonitor(camera_id)
        self._reconnect = ReconnectPolicy(config.reconnect_delays)
        self._client = RTSPClient(
            url=rtsp_url,
            timeout_seconds=config.timeout_seconds,
            frame_width=config.frame_width,
            frame_height=config.frame_height,
        )
        self._grabber = FrameGrabber(
            camera_id=camera_id,
            rtsp_client=self._client,
            frame_buffer=self._buffer,
            fps_monitor=self._fps,
            health_monitor=self._health,
            target_fps=config.target_fps,
            on_frame=self._on_frame,
        )

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

    @property
    def frame_buffer(self) -> FrameBuffer:
        """Buffer frame của camera."""
        return self._buffer

    def set_frame_sink(self, sink: Optional[Callable]) -> None:
        """Cập nhật callback frame (evidence sink)."""
        self._on_frame = sink
        self._grabber.set_frame_sink(sink)

    @property
    def is_running(self) -> bool:
        """Worker thread còn chạy không."""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """
        Khởi động worker thread.

        Raises:
            RuntimeError: Nếu worker đã chạy.
        """
        with self._lock:
            if self.is_running:
                raise RuntimeError(f"CameraWorker {self.camera_id} đang chạy.")
            self._stop_event.clear()
            self._health.set_running(True)
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"camera-worker-{self.camera_id}",
                daemon=True,
            )
            self._thread.start()
            logger.info("CameraWorker started | camera_id={}", self.camera_id)

    def stop(self, timeout: float = 5.0) -> None:
        """
        Dừng worker và đóng RTSP.

        Args:
            timeout: Thời gian chờ thread kết thúc.
        """
        with self._lock:
            self._stop_event.set()
            self._health.set_running(False)
            self._health.on_disconnected("stopped")
            thread = self._thread

        if thread and thread.is_alive():
            thread.join(timeout=timeout)

        self._client.close()
        with self._lock:
            self._thread = None
        self._notify_status()
        logger.info("CameraWorker stopped | camera_id={}", self.camera_id)

    def restart(self) -> None:
        """Stop rồi start lại worker."""
        self.stop()
        self._buffer.clear()
        self._fps.reset()
        self._reconnect.reset()
        self.start()

    def get_runtime_status(self) -> CameraRuntimeStatus:
        """Lấy snapshot trạng thái runtime."""
        return self._health.get_status(self._fps, self._buffer)

    def get_fps_metrics(self) -> dict[str, float]:
        """
        Metrics FPS chi tiết cho API.

        Returns:
            dict: read/decode time trung bình.
        """
        return {
            "avg_read_time_ms": self._fps.avg_read_time_ms,
            "avg_decode_time_ms": self._fps.avg_decode_time_ms,
        }

    def _run_loop(self) -> None:
        """
        Vòng lặp chính — connect, read frames, auto reconnect.

        Không bao giờ raise ra ngoài thread — tránh crash process.
        """
        logger.info("CameraWorker loop begin | camera_id={}", self.camera_id)
        while not self._stop_event.is_set():
            try:
                if not self._client.is_open:
                    self._connect_with_retry()
                if self._stop_event.is_set():
                    break

                ok = self._grabber.grab_once()
                if not ok:
                    logger.warning(
                        "Frame read failed | camera_id={} — reconnecting",
                        self.camera_id,
                    )
                    self._health.on_disconnected("frame read failed")
                    self._client.close()
                    self._schedule_reconnect()
            except Exception as exc:
                logger.exception(
                    "CameraWorker error | camera_id={} err={}",
                    self.camera_id,
                    exc,
                )
                self._health.on_disconnected(str(exc))
                self._client.close()
                self._schedule_reconnect()

        self._client.close()
        self._health.set_running(False)
        logger.info("CameraWorker loop exit | camera_id={}", self.camera_id)

    def _connect_with_retry(self) -> None:
        """Kết nối RTSP lần đầu trong loop."""
        while not self._stop_event.is_set():
            try:
                self._client.connect()
                self._reconnect.record_success()
                self._health.on_connected()
                self._notify_status()
                logger.info("Camera connected | camera_id={}", self.camera_id)
                return
            except Exception as exc:
                self._health.on_reconnect()
                self._health.on_disconnected(str(exc))
                delay = self._reconnect.next_delay()
                logger.warning(
                    "Camera reconnect | camera_id={} delay={}s err={}",
                    self.camera_id,
                    delay,
                    exc,
                )
                self._notify_status()
                if self._stop_event.wait(delay):
                    return

    def _schedule_reconnect(self) -> None:
        """Chờ backoff rồi reconnect."""
        if self._stop_event.is_set():
            return
        self._health.on_reconnect()
        delay = self._reconnect.next_delay()
        logger.info(
            "Camera scheduled reconnect | camera_id={} delay={}s",
            self.camera_id,
            delay,
        )
        self._notify_status()
        self._stop_event.wait(delay)

    def _notify_status(self) -> None:
        """Callback trạng thái cho manager (sync DB heartbeat)."""
        if self._on_status_change:
            try:
                self._on_status_change(self.get_runtime_status())
            except Exception as exc:
                logger.warning("Status callback error | {}", exc)
