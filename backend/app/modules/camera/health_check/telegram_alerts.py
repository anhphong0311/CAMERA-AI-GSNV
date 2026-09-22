"""Telegram alerts for enabled cameras with an unhealthy stream."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from loguru import logger

from app.core.database import get_session_factory
from app.models.camera import Camera
from app.modules.camera.camera_manager.manager import CameraManager
from app.modules.camera.exceptions import CameraNotRunningError
from app.modules.camera.repositories.camera_repository import CameraRepository
from app.modules.camera.utils.config_loader import CameraStreamConfig
from app.modules.event.config import load_telegram_config
from app.modules.event.telegram.provider import TelegramProvider


@dataclass
class _AlertState:
    unhealthy_since: float | None = None
    alerted: bool = False
    next_attempt_at: float = 0.0


class CameraTelegramAlerts:
    """Poll camera workers; send one outage and one recovery message per incident."""

    def __init__(
        self,
        manager: CameraManager,
        config: CameraStreamConfig,
        provider: TelegramProvider | None = None,
        clock: Callable[[], float] = time.monotonic,
        monitoring_enabled: Callable[[], bool] = lambda: True,
    ) -> None:
        self._manager = manager
        self._config = config
        self._provider = provider or TelegramProvider(load_telegram_config())
        self._chat_id = self._provider._config.chat_id
        self._clock = clock
        self._monitoring_enabled = monitoring_enabled
        self._states: dict[int, _AlertState] = {}
        self._seen_healthy: set[int] = set()

    async def check_once(self) -> None:
        """Read enabled cameras and inspect their live worker status."""
        if not self._monitoring_enabled():
            self._states.clear()
            self._seen_healthy.clear()
            return
        factory = get_session_factory()
        async with factory() as session:
            cameras = await CameraRepository(session).list_enabled()
        for camera in cameras:
            try:
                await self._check_camera(camera)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Camera alert check failed | camera_id={} err={}", camera.id, exc)

        enabled_ids = {camera.id for camera in cameras}
        for camera_id in self._states.keys() - enabled_ids:
            del self._states[camera_id]
        self._seen_healthy.intersection_update(enabled_ids)

    async def _check_camera(self, camera: Camera) -> None:
        reason = self._failure_reason(camera.id)
        state = self._states.setdefault(camera.id, _AlertState())
        now = self._clock()

        if reason is not None:
            if state.unhealthy_since is None:
                state.unhealthy_since = now
            grace = (
                self._config.alert_grace_seconds
                if camera.id in self._seen_healthy
                else self._config.alert_startup_grace_seconds
            )
            if (
                not state.alerted
                and now >= state.next_attempt_at
                and now - state.unhealthy_since >= grace
            ):
                if await self._send(camera, f"🚨 Camera mất kết nối\nLý do: {reason}"):
                    state.alerted = True
                else:
                    state.next_attempt_at = now + 60.0
            return

        self._seen_healthy.add(camera.id)
        state.unhealthy_since = None
        if state.alerted:
            if now >= state.next_attempt_at:
                if await self._send(camera, "✅ Camera đã kết nối lại và có hình ảnh mới"):
                    del self._states[camera.id]
                else:
                    state.next_attempt_at = now + 60.0
        else:
            del self._states[camera.id]

    def _failure_reason(self, camera_id: int) -> str | None:
        try:
            status = self._manager.get_status(camera_id)
        except CameraNotRunningError:
            return "Camera chưa chạy"
        if not status.is_running or not status.is_connected:
            return "Không kết nối được luồng RTSP"
        frame_time = status.last_frame_at
        if frame_time is None:
            return "Chưa nhận được hình ảnh"
        age = (datetime.now(timezone.utc) - frame_time).total_seconds()
        if age > self._config.alert_stale_frame_seconds:
            return "Không có hình ảnh mới"
        return None

    async def _send(self, camera: Camera, detail: str) -> bool:
        if not self._provider.is_ready:
            return False
        label = camera.name or camera.code
        location = f"\nVị trí: {camera.location}" if camera.location else ""
        message = f"{detail}\nCamera: {label} ({camera.code}, ID {camera.id}){location}"
        try:
            result = await asyncio.to_thread(
                self._provider.send_text, self._chat_id, message
            )
            return result.ok
        except Exception as exc:
            logger.warning(
                "Camera Telegram alert failed | camera_id={} error_type={}",
                camera.id,
                type(exc).__name__,
            )
            return False

    async def run(self) -> None:
        while True:
            try:
                await self.check_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Camera alert check failed: {}", exc)
            await asyncio.sleep(self._config.alert_check_interval_seconds)
