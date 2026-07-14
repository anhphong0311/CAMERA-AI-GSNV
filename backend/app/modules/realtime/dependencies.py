"""
Dependency Injection + lifecycle cho Realtime module (Sprint 8).
"""

from __future__ import annotations

from typing import Callable, Optional

from fastapi import Request
from loguru import logger

from app.modules.realtime.pipeline_bridge import create_detection_sink
from app.modules.performance.config.loader import load_performance_config
from app.modules.realtime.broadcaster import RealtimeBroadcaster
from app.modules.realtime.hub import ConnectionManager

_manager: Optional[ConnectionManager] = None
_broadcaster: Optional[RealtimeBroadcaster] = None


async def init_realtime_module(app) -> None:
    """Khởi tạo hub + broadcaster khi startup."""
    global _manager, _broadcaster
    _manager = ConnectionManager()
    _broadcaster = RealtimeBroadcaster(_manager)
    app.state.realtime_manager = _manager
    app.state.realtime_broadcaster = _broadcaster
    _broadcaster.start()
    logger.info("Realtime module initialized (WebSocket hub + broadcaster)")


async def shutdown_realtime_module() -> None:
    """Dừng broadcaster khi shutdown."""
    global _manager, _broadcaster
    if _broadcaster is not None:
        await _broadcaster.stop()
    _broadcaster = None
    _manager = None
    logger.info("Realtime module shutdown complete")


def wire_ai_to_realtime(app) -> None:
    """
    Nối DetectionService → RealtimeBroadcaster (detection thật lên Dashboard).

    Gọi sau init_ai_module + init_realtime_module.
    """
    service = getattr(app.state, "ai_service", None)
    broadcaster: Optional[RealtimeBroadcaster] = getattr(
        app.state, "realtime_broadcaster", None
    )
    if service is None or broadcaster is None:
        logger.warning("Skip wire AI→realtime: module chưa sẵn sàng")
        return

    service.set_detection_sink(create_detection_sink(app, broadcaster))
    logger.info(
        "AI detection wired to realtime (tracking={} behavior={} rules={})",
        load_performance_config().pipeline.chain_tracking,
        load_performance_config().pipeline.chain_behavior,
        load_performance_config().pipeline.chain_rules,
    )


def wire_live_cameras_to_realtime(app) -> None:
    """Cung cấp trạng thái camera DB cho /realtime/cameras khi tắt demo."""
    broadcaster: Optional[RealtimeBroadcaster] = getattr(
        app.state, "realtime_broadcaster", None
    )
    camera_service = getattr(app.state, "camera_service", None)
    if broadcaster is None or camera_service is None:
        return

    async def _fetch_status() -> list[dict]:
        cameras = await camera_service.list_cameras(limit=500)
        return [
            {
                "camera_id": c.id,
                "name": c.name or c.code,
                "status": "online" if c.status == "online" else "offline",
                "fps": float(c.fps or 0),
            }
            for c in cameras
        ]

    broadcaster.set_camera_fetcher(_fetch_status)
    logger.info("Live camera fetcher registered for realtime module")


def get_manager(request: Request) -> ConnectionManager:
    """WS hub từ app.state."""
    manager: Optional[ConnectionManager] = getattr(
        request.app.state, "realtime_manager", None
    )
    if manager is None:
        raise RuntimeError("Realtime hub chưa được khởi tạo.")
    return manager


def get_broadcaster(request: Request) -> RealtimeBroadcaster:
    """Broadcaster từ app.state."""
    b: Optional[RealtimeBroadcaster] = getattr(
        request.app.state, "realtime_broadcaster", None
    )
    if b is None:
        raise RuntimeError("Broadcaster chưa được khởi tạo.")
    return b
