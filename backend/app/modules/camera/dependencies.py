"""
Dependency Injection + lifecycle cho CameraManager.

Khởi tạo manager khi app startup, gắn heartbeat sync vào DB.
"""

import asyncio
from typing import Annotated, Optional

from fastapi import Depends, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.dependencies import DbSession
from app.modules.camera.camera_manager.manager import CameraManager
from app.modules.camera.models.frame import CameraRuntimeStatus
from app.modules.camera.services.camera_service import CameraService
from app.modules.camera.utils.config_loader import CameraStreamConfig, load_camera_config

# Singleton manager trong app.state
_manager: Optional[CameraManager] = None


def _schedule_heartbeat(status: CameraRuntimeStatus) -> None:
    """
    Callback sync từ worker thread — schedule coroutine ghi DB.

    Args:
        status: Runtime status snapshot.
    """
    if _manager is None or _manager._loop is None:
        return
    asyncio.run_coroutine_threadsafe(_persist_heartbeat(status), _manager._loop)


async def _persist_heartbeat(status: CameraRuntimeStatus) -> None:
    """Ghi heartbeat vào PostgreSQL (session mới mỗi lần)."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            manager = get_camera_manager_from_state()
            if manager is None:
                return
            service = CameraService(session, manager)
            await service.sync_runtime_status(status)
    except Exception as exc:
        logger.warning("Heartbeat persist failed | camera_id={} err={}", status.camera_id, exc)


async def init_camera_module(app) -> CameraManager:
    """
    Khởi tạo CameraManager và auto-start camera enabled.

    Args:
        app: FastAPI application instance.

    Returns:
        CameraManager: Manager đã sẵn sàng.
    """
    global _manager
    config = load_camera_config()
    _manager = CameraManager(config=config, on_status_change=_schedule_heartbeat)
    _manager.set_event_loop(asyncio.get_running_loop())
    app.state.camera_manager = _manager
    app.state.camera_config = config

    factory = get_session_factory()
    async with factory() as session:
        service = CameraService(session, _manager, config)
        count = await service.bootstrap_enabled_cameras()
        logger.info("Camera module bootstrapped | auto_started={}", count)

    return _manager


async def shutdown_camera_module() -> None:
    """Dừng tất cả camera workers khi app shutdown."""
    global _manager
    if _manager is not None:
        _manager.stop_all()
        _manager = None
        logger.info("Camera module shutdown complete")


def get_camera_manager_from_state() -> Optional[CameraManager]:
    """Lấy manager từ biến module (dùng trong heartbeat)."""
    return _manager


def get_camera_manager(request: Request) -> CameraManager:
    """
    FastAPI dependency — CameraManager từ app.state.

    Raises:
        RuntimeError: Module chưa khởi tạo.
    """
    manager: Optional[CameraManager] = getattr(request.app.state, "camera_manager", None)
    if manager is None:
        raise RuntimeError("CameraManager chưa được khởi tạo.")
    return manager


def get_camera_service(
    session: DbSession,
    manager: Annotated[CameraManager, Depends(get_camera_manager)],
) -> CameraService:
    """Factory inject CameraService."""
    config: CameraStreamConfig = load_camera_config()
    return CameraService(session, manager, config)
