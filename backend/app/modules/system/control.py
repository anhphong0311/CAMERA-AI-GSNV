"""
SystemControlService — bật/tắt toàn bộ pipeline giám sát.

TẮT: dừng camera + AI pipeline + orchestrator (+ tạm dừng event bridge).
BẬT: khôi phục lại các thành phần trên.

Giữ API + Telegram bot chạy để vẫn nhận lệnh /bat sau khi đã /tat.
Trạng thái lưu file để restart container vẫn nhớ đang tắt.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional

from loguru import logger


def _default_state_path() -> Path:
    return Path(os.getenv("SYSTEM_STATE_PATH", "logs/system_state.json"))


def _public_base_url() -> str:
    return os.getenv("AEMS_PUBLIC_URL", "http://localhost:8080").rstrip("/")


def viewing_links_text(base_url: Optional[str] = None) -> str:
    """Đường link xem dashboard / live / cảnh báo."""
    base = (base_url or _public_base_url()).rstrip("/")
    return (
        "🔗 Đường link xem:\n"
        f"• Dashboard: {base}/\n"
        f"• Live Camera: {base}/live\n"
        f"• Live Detection: {base}/detection\n"
        f"• Cảnh báo: {base}/alerts\n"
        f"• Quản lý camera: {base}/cameras"
    )


class SystemControlService:
    """Điều khiển vòng đời giám sát (không tắt process backend)."""

    def __init__(self, app: Any, state_path: Optional[Path] = None) -> None:
        self._app = app
        self._state_path = Path(state_path) if state_path else _default_state_path()
        self._lock = asyncio.Lock()
        self._monitoring = True
        self._load_state()

    @property
    def is_monitoring(self) -> bool:
        return self._monitoring

    def status_text(self) -> str:
        cams = 0
        pipeline = False
        orchestrator = False
        try:
            manager = getattr(self._app.state, "camera_manager", None)
            if manager is not None:
                cams = len(manager.list_running_ids())
        except Exception:
            pass
        try:
            ai = getattr(self._app.state, "ai_service", None)
            if ai is not None:
                pipeline = bool(ai.get_statistics().get("pipeline_running"))
        except Exception:
            pass
        try:
            perf = getattr(self._app.state, "performance", None)
            if perf is not None:
                orchestrator = bool(getattr(perf.orchestrator, "_running", False))
        except Exception:
            pass

        icon = "🟢" if self._monitoring else "🔴"
        state = "ĐANG BẬT" if self._monitoring else "ĐANG TẮT"
        return (
            f"{icon} Hệ thống giám sát: {state}\n"
            f"Camera đang chạy: {cams}\n"
            f"AI pipeline: {'on' if pipeline else 'off'}\n"
            f"Orchestrator: {'on' if orchestrator else 'off'}\n"
            f"(API + Telegram bot vẫn hoạt động để nhận lệnh)"
        )

    async def turn_off(self) -> str:
        async with self._lock:
            if not self._monitoring:
                return "🔴 Hệ thống đã tắt sẵn.\nGõ /bat hoặc /system_on để bật lại."

            logger.warning("System OFF requested via control service")
            errors: list[str] = []

            # 1) Dừng bridge camera → AI
            try:
                perf = getattr(self._app.state, "performance", None)
                if perf is not None:
                    await perf.orchestrator.stop()
            except Exception as exc:
                errors.append(f"orchestrator: {exc}")
                logger.exception("System OFF orchestrator failed")

            # 2) Dừng AI workers
            try:
                ai = getattr(self._app.state, "ai_service", None)
                if ai is not None:
                    ai.stop_pipeline()
            except Exception as exc:
                errors.append(f"ai: {exc}")
                logger.exception("System OFF AI failed")

            # 3) Dừng toàn bộ camera RTSP
            try:
                manager = getattr(self._app.state, "camera_manager", None)
                if manager is not None:
                    manager.stop_all()
            except Exception as exc:
                errors.append(f"cameras: {exc}")
                logger.exception("System OFF cameras failed")

            self._monitoring = False
            self._save_state()

            if errors:
                return (
                    "⚠️ Đã yêu cầu TẮT hệ thống nhưng có lỗi:\n"
                    + "\n".join(f"- {e}" for e in errors)
                    + "\n"
                    + self.status_text()
                )
            return (
                "🔴 Đã TẮT toàn bộ hệ thống giám sát.\n"
                "Camera / AI / pipeline đã dừng.\n"
                "Gõ /bat hoặc /system_on để bật lại."
            )

    async def turn_on(self) -> str:
        async with self._lock:
            if self._monitoring:
                return (
                    "🟢 Hệ thống đang bật sẵn.\n"
                    f"{viewing_links_text()}\n"
                    "Gõ /tat hoặc /system_off để tắt."
                )

            logger.warning("System ON requested via control service")
            errors: list[str] = []

            # 1) AI pipeline
            try:
                ai = getattr(self._app.state, "ai_service", None)
                if ai is not None:
                    ai.start_pipeline()
            except Exception as exc:
                errors.append(f"ai: {exc}")
                logger.exception("System ON AI failed")

            # 2) Orchestrator
            try:
                perf = getattr(self._app.state, "performance", None)
                if perf is not None:
                    await perf.orchestrator.start()
            except Exception as exc:
                errors.append(f"orchestrator: {exc}")
                logger.exception("System ON orchestrator failed")

            # 3) Bootstrap camera enabled
            started = 0
            try:
                from app.core.database import get_session_factory
                from app.modules.camera.services.camera_service import CameraService
                from app.modules.camera.utils.config_loader import load_camera_config

                manager = getattr(self._app.state, "camera_manager", None)
                if manager is not None:
                    config = getattr(self._app.state, "camera_config", None) or load_camera_config()
                    # Tạm bật auto-start để bootstrap khi bật lại thủ công
                    prev = config.auto_start_enabled
                    config.auto_start_enabled = True
                    factory = get_session_factory()
                    async with factory() as session:
                        service = CameraService(session, manager, config)
                        started = await service.bootstrap_enabled_cameras()
                    config.auto_start_enabled = prev
            except Exception as exc:
                errors.append(f"cameras: {exc}")
                logger.exception("System ON cameras failed")

            self._monitoring = True
            self._save_state()

            links = viewing_links_text()
            if errors:
                return (
                    "⚠️ Đã yêu cầu BẬT hệ thống nhưng có lỗi:\n"
                    + "\n".join(f"- {e}" for e in errors)
                    + "\n"
                    + self.status_text()
                    + "\n"
                    + links
                )
            return (
                f"🟢 Đã BẬT toàn bộ hệ thống giám sát.\n"
                f"Đã khởi động {started} camera.\n"
                f"{links}\n"
                f"Gõ /tat hoặc /system_off để tắt."
            )

    async def apply_persisted_state(self) -> None:
        """Sau startup: nếu lần trước đang tắt thì tắt lại."""
        if self._monitoring:
            return
        logger.warning("Restoring persisted OFF state — shutting monitoring down")
        # Force path: mark as on temporarily so turn_off runs
        self._monitoring = True
        await self.turn_off()

    def _load_state(self) -> None:
        try:
            if not self._state_path.exists():
                return
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._monitoring = bool(data.get("monitoring", True))
            logger.info(
                "System state loaded | monitoring={} path={}",
                self._monitoring,
                self._state_path,
            )
        except Exception as exc:
            logger.warning("System state load failed: {}", exc)
            self._monitoring = True

    def _save_state(self) -> None:
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"monitoring": self._monitoring}
            self._state_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("System state save failed: {}", exc)


async def init_system_control(app: Any) -> SystemControlService:
    """Gắn SystemControlService vào app.state và áp dụng trạng thái đã lưu."""
    service = SystemControlService(app)
    app.state.system_control = service

    event_service = getattr(app.state, "event_service", None)
    if event_service is not None and hasattr(event_service, "bind_system_control"):
        event_service.bind_system_control(service)

    await service.apply_persisted_state()
    logger.info(
        "System control initialized | monitoring={}",
        service.is_monitoring,
    )
    return service
