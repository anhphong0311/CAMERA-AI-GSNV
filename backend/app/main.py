"""
FastAPI application entry point.

Khởi tạo app, lifespan (DB + Redis), middleware, exception handlers, routes.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from loguru import logger

from app.api import api_router
from app.config.settings import get_settings
from app.core.database import close_db, init_db
from app.core.logging import setup_logging
from app.core.redis import close_redis, init_redis
from app.exceptions import register_exception_handlers
from app.middleware import register_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Quản lý vòng đời ứng dụng — startup và shutdown.

    Startup: logging, DB engine, Redis client.
    Shutdown: đóng kết nối tài nguyên.
    """
    settings = get_settings()
    setup_logging()
    logger.info("Starting {} | env={}", settings.project_name, settings.environment)

    init_db()
    await init_redis()
    logger.info("Database and Redis initialized")

    from app.modules.camera.dependencies import init_camera_module, shutdown_camera_module
    from app.modules.ai.dependencies import init_ai_module, shutdown_ai_module
    from app.modules.tracking.dependencies import (
        init_tracking_module,
        shutdown_tracking_module,
    )
    from app.modules.behavior.dependencies import (
        init_behavior_module,
        shutdown_behavior_module,
    )
    from app.modules.rule_engine.dependencies import (
        init_rule_engine_module,
        shutdown_rule_engine_module,
    )
    from app.modules.event.dependencies import (
        init_event_module,
        shutdown_event_module,
    )
    from app.modules.realtime.dependencies import (
        init_realtime_module,
        shutdown_realtime_module,
        wire_ai_to_realtime,
        wire_live_cameras_to_realtime,
    )
    from app.modules.admin.dependencies import (
        init_admin_module,
        shutdown_admin_module,
    )
    from app.modules.performance.dependencies import (
        init_performance_module,
        shutdown_performance_module,
    )

    await init_camera_module(app)
    logger.info("Camera module initialized")

    await init_ai_module(app)
    logger.info("AI Detection module initialized")

    await init_tracking_module(app)
    logger.info("Tracking module initialized")

    await init_behavior_module(app)
    logger.info("Behavior Feature module initialized")

    await init_rule_engine_module(app)
    logger.info("Rule Engine module initialized")

    await init_event_module(app)
    logger.info("Event Processing module initialized")

    await init_realtime_module(app)
    wire_ai_to_realtime(app)
    wire_live_cameras_to_realtime(app)
    logger.info("Realtime module initialized")

    await init_admin_module(app)
    logger.info("Admin (Enterprise) module initialized")

    from app.modules.ml_platform.dependencies import (
        init_ml_platform_module,
        shutdown_ml_platform_module,
    )

    await init_ml_platform_module(app)
    logger.info("ML Platform module initialized (v2.0 Sprint 13)")

    await init_performance_module(app)
    logger.info("Performance module initialized")

    from app.modules.system.control import init_system_control

    await init_system_control(app)
    logger.info("System control initialized")

    camera_alert_task = None
    camera_config = app.state.camera_config
    if camera_config.telegram_alerts_enabled:
        from app.modules.camera.health_check.telegram_alerts import CameraTelegramAlerts

        camera_alert_task = asyncio.create_task(
            CameraTelegramAlerts(
                app.state.camera_manager,
                camera_config,
                monitoring_enabled=lambda: app.state.system_control.is_monitoring,
            ).run()
        )
        logger.info("Camera Telegram alert monitor initialized")

    yield

    if camera_alert_task is not None:
        camera_alert_task.cancel()
        try:
            await camera_alert_task
        except asyncio.CancelledError:
            pass
    await shutdown_performance_module(app)
    await shutdown_ml_platform_module(app)
    await shutdown_admin_module(app)
    await shutdown_realtime_module()
    await shutdown_event_module()
    await shutdown_rule_engine_module()
    await shutdown_behavior_module()
    await shutdown_tracking_module()
    await shutdown_ai_module()
    await shutdown_camera_module()
    await close_redis()
    await close_db()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory — tạo FastAPI instance.

    Pattern factory giúp test dễ dàng (inject app mới mỗi test case).

    Returns:
        FastAPI: Ứng dụng đã cấu hình đầy đủ.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.project_name,
        description="AI Employee Monitoring System — v2.0 ML Training Platform (Sprint 13)",
        version="2.0.0-sprint13",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    register_middleware(app)
    register_exception_handlers(app)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint — redirect info tới docs."""
        return {
            "project": settings.project_name,
            "docs": "/api/v1/docs",
            "health": "/api/v1/health",
        }

    return app


app = create_app()
