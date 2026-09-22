"""
CameraService — business logic CRUD + điều khiển stream qua CameraManager.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundError
from app.modules.camera.camera_manager.manager import CameraManager
from app.modules.camera.exceptions import CameraNotRunningError, FrameBufferEmptyError
from app.modules.camera.models.frame import CameraRuntimeStatus
from app.modules.camera.repositories.camera_repository import CameraRepository
from app.modules.camera.schemas.camera import (
    CameraCreate,
    CameraFPSRead,
    CameraFrameRead,
    CameraHealthRead,
    CameraRead,
    CameraUpdate,
)
from app.modules.camera.utils.config_loader import CameraStreamConfig, load_camera_config
from app.modules.camera.utils.frame_codec import encode_frame_base64

# Cache JPEG preview theo (camera_id → frame_id) — tránh encode lại cùng frame
_preview_cache: Dict[int, Tuple[int, CameraFrameRead]] = {}
_preview_lock = threading.Lock()


class CameraService:
    """
    Service layer — orchestrate Repository + CameraManager.

    API layer chỉ gọi service, không trực tiếp thao tác worker/thread.
    """

    def __init__(
        self,
        session: AsyncSession,
        manager: CameraManager,
        config: Optional[CameraStreamConfig] = None,
    ) -> None:
        self._session = session
        self._repo = CameraRepository(session)
        self._manager = manager
        self._config = config or load_camera_config()

    async def list_cameras(self, skip: int = 0, limit: int = 100) -> List[CameraRead]:
        """Danh sách camera từ DB."""
        cameras = await self._repo.list_all(skip=skip, limit=limit)
        return [CameraRead.model_validate(c) for c in cameras]

    async def get_camera(self, camera_id: int) -> CameraRead:
        """Chi tiết camera."""
        camera = await self._repo.get_by_id(camera_id)
        if camera is None:
            raise NotFoundError("Camera", camera_id)
        return CameraRead.model_validate(camera)

    async def create_camera(self, data: CameraCreate) -> CameraRead:
        """
        Tạo camera DB + register URL vào manager.

        Không auto-start — client gọi POST /start riêng.
        """
        camera = await self._repo.create(data)
        await self._session.commit()
        rtsp = CameraRepository.resolve_rtsp_url(camera)
        self._manager.register_camera(camera.id, rtsp)
        logger.info("Camera created | id={} code={}", camera.id, camera.code)
        return CameraRead.model_validate(camera)

    async def update_camera(self, camera_id: int, data: CameraUpdate) -> CameraRead:
        """Cập nhật camera, chỉ thay đổi worker khi URL hoặc enabled đổi."""
        previous = await self._repo.get_by_id(camera_id)
        if previous is None:
            raise NotFoundError("Camera", camera_id)
        previous_url = CameraRepository.resolve_rtsp_url(previous)
        previously_enabled = previous.enabled
        was_running = camera_id in self._manager.list_running_ids()
        camera = await self._repo.update(camera_id, data)
        rtsp = CameraRepository.resolve_rtsp_url(camera)
        self._manager.register_camera(camera.id, rtsp)
        if not camera.enabled:
            if was_running:
                await asyncio.to_thread(self._manager.stop_camera, camera.id)
            await self._repo.update_heartbeat(camera.id, "offline")
        elif camera.enabled and was_running and rtsp != previous_url:
            # stop/release VideoCapture có thể block vài giây.
            await asyncio.to_thread(self._manager.reload_camera, camera.id, rtsp)
        elif camera.enabled and not previously_enabled and not was_running:
            await asyncio.to_thread(self._manager.start_camera, camera.id, rtsp)
        await self._session.commit()
        await self._session.refresh(camera)
        return CameraRead.model_validate(camera)

    async def delete_camera(self, camera_id: int) -> None:
        """Dừng worker (nếu có) và xóa DB."""
        await self._repo.delete(camera_id)
        await asyncio.to_thread(self._manager.unregister_camera, camera_id)
        await self._session.commit()
        logger.info("Camera deleted | id={}", camera_id)

    async def start_stream(self, camera_id: int) -> CameraRuntimeStatus:
        """
        Bắt đầu đọc RTSP cho camera.

        Args:
            camera_id: ID camera.

        Returns:
            CameraRuntimeStatus sau khi start.
        """
        camera = await self._repo.get_by_id(camera_id)
        if camera is None:
            raise NotFoundError("Camera", camera_id)
        rtsp = CameraRepository.resolve_rtsp_url(camera)
        self._manager.register_camera(camera_id, rtsp)
        self._manager.start_camera(camera_id, rtsp_url=rtsp)
        await self._repo.update_heartbeat(
            camera_id, "reconnecting", set_online=False
        )
        await self._session.commit()
        return self._manager.get_status(camera_id)

    def stop_stream(self, camera_id: int) -> None:
        """Dừng worker camera."""
        self._manager.stop_camera(camera_id)

    async def stop_stream_async(self, camera_id: int) -> None:
        """Dừng worker và cập nhật DB status offline."""
        await asyncio.to_thread(self.stop_stream, camera_id)
        await self._repo.update_heartbeat(camera_id, "offline")
        await self._session.commit()

    async def restart_stream(self, camera_id: int) -> CameraRuntimeStatus:
        """Restart worker."""
        await asyncio.to_thread(self._manager.restart_camera, camera_id)
        return self._manager.get_status(camera_id)

    async def get_health(self, camera_id: int) -> CameraHealthRead:
        """
        Health tổng hợp DB + runtime.

        Nếu worker không chạy, chỉ trả DB status.
        """
        camera = await self._repo.get_by_id(camera_id)
        if camera is None:
            raise NotFoundError("Camera", camera_id)

        runtime: dict = {"status": "offline", "is_running": False}
        try:
            status = self._manager.get_status(camera_id)
            runtime = status.to_dict()
        except CameraNotRunningError:
            pass

        return CameraHealthRead(
            camera_id=camera_id,
            db_status=camera.status,
            runtime=runtime,
            last_online=camera.last_online,
            last_heartbeat=camera.last_heartbeat,
        )

    def get_fps(self, camera_id: int) -> CameraFPSRead:
        """Metrics FPS từ worker."""
        worker = self._manager.get_worker(camera_id)
        status = worker.get_runtime_status()
        metrics = worker.get_fps_metrics()
        return CameraFPSRead(
            camera_id=camera_id,
            current_fps=status.current_fps,
            average_fps=status.average_fps,
            read_time_ms=metrics["avg_read_time_ms"],
            decode_time_ms=metrics["avg_decode_time_ms"],
            queue_size=status.queue_size,
            target_fps=self._config.target_fps,
        )

    def get_latest_frame(self, camera_id: int) -> CameraFrameRead:
        """
        Lấy frame mới nhất từ buffer — encode JPEG base64 (có cache theo frame_id).

        Raises:
            FrameBufferEmptyError: Chưa có frame.
        """
        worker = self._manager.get_worker(camera_id)
        packet = worker.frame_buffer.latest()
        if packet is None:
            raise FrameBufferEmptyError()

        with _preview_lock:
            cached = _preview_cache.get(camera_id)
            if cached is not None and cached[0] == packet.frame_id:
                return cached[1]

        quality = getattr(self._config, "preview_jpeg_quality", 60)
        max_width = getattr(self._config, "preview_max_width", 960)
        b64 = encode_frame_base64(
            packet.data, quality=quality, max_width=max_width
        )
        # width/height sau khi resize preview
        if max_width > 0 and packet.width > max_width:
            scale = max_width / float(packet.width)
            out_w, out_h = max_width, max(1, int(round(packet.height * scale)))
        else:
            out_w, out_h = packet.width, packet.height

        result = CameraFrameRead(
            camera_id=camera_id,
            frame_id=packet.frame_id,
            timestamp=packet.timestamp,
            width=out_w,
            height=out_h,
            image_base64=b64,
        )
        with _preview_lock:
            _preview_cache[camera_id] = (packet.frame_id, result)
        return result

    async def sync_runtime_status(self, status: CameraRuntimeStatus) -> None:
        """
        Ghi heartbeat từ worker callback vào DB.

        Args:
            status: Snapshot runtime từ HealthMonitor.
        """
        set_online = status.is_connected and status.status == "online"
        await self._repo.update_heartbeat(
            status.camera_id,
            status.status,
            set_online=set_online,
        )
        await self._session.commit()

    async def bootstrap_enabled_cameras(self) -> int:
        """
        Auto-start camera enabled=true khi app khởi động.

        Returns:
            int: Số camera đã start.
        """
        if not self._config.auto_start_enabled:
            return 0
        cameras = await self._repo.list_enabled()
        started = 0
        for cam in cameras:
            rtsp = CameraRepository.resolve_rtsp_url(cam)
            self._manager.register_camera(cam.id, rtsp)
            try:
                self._manager.start_camera(cam.id, rtsp_url=rtsp)
                started += 1
            except Exception as exc:
                logger.warning(
                    "Auto-start failed | camera_id={} err={}", cam.id, exc
                )
        return started
