"""
Dependency Injection + lifecycle cho Event Processing Center.

Khởi tạo EventService, chạy background loop:
- Lấy BehaviorEvent từ Rule Engine AlertQueue (Sprint 6) → ingest.
- Xử lý event + gửi notification (offload sang thread để không block event loop).
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import Request
from loguru import logger

from app.modules.event.services import EventService
from app.modules.event.telegram.poller import TelegramCommandPoller

_service: Optional[EventService] = None
_task: Optional[asyncio.Task] = None
_poller: Optional[TelegramCommandPoller] = None


async def _bridge_loop(app, interval: float = 1.0) -> None:
    """Bơm event từ Rule Engine AlertQueue → Event Center theo chu kỳ."""
    service: EventService = app.state.event_service
    # PHONE/AWAY gửi khi FINISHED (có giờ từ–đến); rule khác gửi khi CONFIRMED
    _accept_states = {"CONFIRMED", "FINISHED", "ENDED"}
    while True:
        try:
            if not service.is_monitoring():
                await asyncio.sleep(interval)
                continue
            rule_service = getattr(app.state, "rule_service", None)
            if rule_service is not None:
                for ev in rule_service.alert_queue().pop_all():
                    state_val = getattr(ev.state, "value", str(ev.state))
                    if state_val not in _accept_states:
                        continue
                    service.ingest_dict(ev.to_dict())
            # xử lý + gửi trong threadpool (cv2/httpx là blocking)
            await asyncio.to_thread(service.run_once)
        except asyncio.CancelledError:  # pragma: no cover
            break
        except Exception as exc:  # pragma: no cover
            logger.warning("Event bridge loop lỗi: {}", exc)
        await asyncio.sleep(interval)


async def init_event_module(app) -> EventService:
    """Khởi tạo Event Processing Center khi app startup."""
    global _service, _task, _poller
    service = EventService()
    _service = service
    app.state.event_service = service
    wire_evidence_frame_sink(app)
    _task = asyncio.create_task(_bridge_loop(app))

    if service.telegram_status()["ready"]:
        _poller = TelegramCommandPoller(
            service._telegram_config,
            service,
            command_handler=service.handle_command,
        )
        _poller.start()

    logger.info(
        "Event module initialized (telegram_ready={} poller={})",
        service.telegram_status()["ready"],
        _poller.running if _poller else False,
    )
    return service


async def shutdown_event_module() -> None:
    """Dọn dẹp khi shutdown."""
    global _service, _task, _poller
    if _poller is not None:
        await _poller.stop()
    _poller = None
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except (asyncio.CancelledError, Exception):  # pragma: no cover
            pass
    _task = None
    if _service is not None:
        _service.shutdown()
    _service = None
    logger.info("Event module shutdown complete")


def get_event_service(request: Request) -> EventService:
    """FastAPI dependency — EventService từ app.state."""
    service: Optional[EventService] = getattr(
        request.app.state, "event_service", None
    )
    if service is None:
        raise RuntimeError("EventService chưa được khởi tạo.")
    return service


def wire_evidence_frame_sink(app) -> None:
    """Gắn camera frame → evidence buffer (không đọc lại RTSP)."""
    manager = getattr(app.state, "camera_manager", None)
    service: Optional[EventService] = getattr(app.state, "event_service", None)
    if manager is None or service is None:
        return

    def _on_frame(camera_id: int, packet) -> None:
        try:
            service.push_frame(
                camera_id,
                packet.data,
                packet.timestamp,
                packet.frame_id,
            )
        except Exception as exc:
            logger.debug("Evidence frame sink skipped cam={}: {}", camera_id, exc)

    manager.set_frame_sink(_on_frame)
    logger.info("Evidence frame sink wired to CameraManager")
