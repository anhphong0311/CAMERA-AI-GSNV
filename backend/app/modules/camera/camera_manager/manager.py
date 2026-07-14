"""
CameraManager — điều phối multi-camera workers.

Thiết kế scale: mỗi camera một CameraWorker độc lập.
Bulkhead — camera A lỗi không ảnh hưởng camera B.
"""

import asyncio
import threading
from typing import Callable, Dict, Optional

from loguru import logger

from app.modules.camera.exceptions import (
    CameraAlreadyRunningError,
    CameraNotFoundError,
    CameraNotRunningError,
)
from app.modules.camera.models.frame import CameraRuntimeStatus
from app.modules.camera.stream_worker.worker import CameraWorker
from app.modules.camera.utils.config_loader import CameraStreamConfig


class CameraManager:
    """
    Singleton-like manager — quản lý dict camera_id → CameraWorker.

    Thread-safe cho start/stop từ API async (FastAPI) và worker threads.
    """

    def __init__(
        self,
        config: Optional[CameraStreamConfig] = None,
        on_status_change: Optional[Callable[[CameraRuntimeStatus], None]] = None,
    ) -> None:
        self._config = config or CameraStreamConfig()
        self._workers: Dict[int, CameraWorker] = {}
        self._rtsp_urls: Dict[int, str] = {}
        self._lock = threading.RLock()
        self._on_status_change = on_status_change
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._frame_sink: Optional[Callable] = None

    def set_frame_sink(self, sink: Callable) -> None:
        """Callback mỗi frame mới — dùng cho Evidence Engine."""
        self._frame_sink = sink
        with self._lock:
            for worker in self._workers.values():
                worker.set_frame_sink(sink)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Gắn event loop chính để schedule async heartbeat callback."""
        self._loop = loop

    def register_camera(self, camera_id: int, rtsp_url: str) -> None:
        """
        Đăng ký URL RTSP cho camera (chưa start worker).

        Args:
            camera_id: ID camera DB.
            rtsp_url: URL RTSP ưu tiên sub stream nếu có.
        """
        with self._lock:
            self._rtsp_urls[camera_id] = rtsp_url

    def unregister_camera(self, camera_id: int) -> None:
        """Dừng và gỡ camera khỏi manager."""
        self.stop_camera(camera_id)
        with self._lock:
            self._rtsp_urls.pop(camera_id, None)

    def start_camera(self, camera_id: int, rtsp_url: Optional[str] = None) -> None:
        """
        Khởi động worker cho camera.

        Args:
            camera_id: ID camera.
            rtsp_url: Override URL; nếu None dùng URL đã register.

        Raises:
            CameraAlreadyRunningError: Worker đã chạy.
            CameraNotFoundError: Không có RTSP URL.
        """
        with self._lock:
            if camera_id in self._workers and self._workers[camera_id].is_running:
                raise CameraAlreadyRunningError(camera_id)

            url = rtsp_url or self._rtsp_urls.get(camera_id)
            if not url:
                raise CameraNotFoundError(camera_id)

            worker = CameraWorker(
                camera_id=camera_id,
                rtsp_url=url,
                config=self._config,
                on_status_change=self._handle_status_change,
                on_frame=self._frame_sink,
            )
            worker.start()
            self._workers[camera_id] = worker
            self._rtsp_urls[camera_id] = url
            logger.info("CameraManager started | camera_id={}", camera_id)

    def stop_camera(self, camera_id: int) -> None:
        """
        Dừng worker camera.

        Nếu worker tồn tại (dù đang chạy hay đã tự dừng), luôn stop + gỡ
        khỏi registry một cách graceful. Chỉ raise khi camera chưa từng
        được start (không có worker) để phân biệt lỗi gọi sai.

        Raises:
            CameraNotRunningError: Không có worker cho camera_id.
        """
        with self._lock:
            worker = self._workers.get(camera_id)
            if worker is None:
                raise CameraNotRunningError(camera_id)
            worker.stop()
            del self._workers[camera_id]
            logger.info("CameraManager stopped | camera_id={}", camera_id)

    def restart_camera(self, camera_id: int) -> None:
        """Restart worker — stop + start."""
        url = self._rtsp_urls.get(camera_id)
        try:
            self.stop_camera(camera_id)
        except CameraNotRunningError:
            pass
        self.start_camera(camera_id, rtsp_url=url)

    def reload_camera(self, camera_id: int, rtsp_url: str) -> None:
        """
        Cập nhật URL và restart worker.

        Args:
            camera_id: ID camera.
            rtsp_url: URL RTSP mới.
        """
        self.register_camera(camera_id, rtsp_url)
        if camera_id in self._workers:
            self.restart_camera(camera_id)
        else:
            self.start_camera(camera_id, rtsp_url=rtsp_url)

    def get_worker(self, camera_id: int) -> CameraWorker:
        """
        Lấy worker instance.

        Raises:
            CameraNotRunningError: Worker không chạy.
        """
        with self._lock:
            worker = self._workers.get(camera_id)
            if worker is None:
                raise CameraNotRunningError(camera_id)
            return worker

    def get_status(self, camera_id: int) -> CameraRuntimeStatus:
        """
        Trạng thái runtime camera.

        Raises:
            CameraNotRunningError: Worker chưa chạy.
        """
        return self.get_worker(camera_id).get_runtime_status()

    def list_running_ids(self) -> list[int]:
        """Danh sách camera_id đang có worker active."""
        with self._lock:
            return [cid for cid, w in self._workers.items() if w.is_running]

    def stop_all(self) -> None:
        """Dừng tất cả workers — gọi khi app shutdown."""
        with self._lock:
            ids = list(self._workers.keys())
        for cid in ids:
            try:
                self.stop_camera(cid)
            except CameraNotRunningError:
                pass
        logger.info("CameraManager stopped all workers")

    def _handle_status_change(self, status: CameraRuntimeStatus) -> None:
        """Forward status tới callback (async heartbeat)."""
        if self._on_status_change:
            self._on_status_change(status)
