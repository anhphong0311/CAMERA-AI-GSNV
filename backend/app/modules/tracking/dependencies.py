"""
Dependency Injection + lifecycle cho Tracking module.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request
from loguru import logger

from app.modules.tracking.benchmark.benchmark_service import BenchmarkService
from app.modules.tracking.config import load_tracking_config
from app.modules.tracking.services.tracking_service import TrackingService

_service: Optional[TrackingService] = None


async def init_tracking_module(app) -> TrackingService:
    """
    Khởi tạo Tracking Engine khi app startup.

    - Load tracking.yaml.
    - Tạo TrackingService (engine tạo lazy theo camera khi có dữ liệu).

    Args:
        app: FastAPI application.

    Returns:
        TrackingService.
    """
    global _service
    config = load_tracking_config()
    _service = TrackingService(config)
    app.state.tracking_service = _service
    app.state.tracking_config = config
    logger.info("Tracking module initialized")
    return _service


async def shutdown_tracking_module() -> None:
    """Dọn dẹp khi shutdown."""
    global _service
    _service = None
    logger.info("Tracking module shutdown complete")


def get_tracking_service(request: Request) -> TrackingService:
    """FastAPI dependency — TrackingService từ app.state."""
    service: Optional[TrackingService] = getattr(
        request.app.state, "tracking_service", None
    )
    if service is None:
        raise RuntimeError("TrackingService chưa được khởi tạo.")
    return service


def get_tracking_benchmark_service(request: Request) -> BenchmarkService:
    """FastAPI dependency — BenchmarkService tracking."""
    config = getattr(request.app.state, "tracking_config", None)
    if config is None:
        config = load_tracking_config()
    return BenchmarkService(config)
