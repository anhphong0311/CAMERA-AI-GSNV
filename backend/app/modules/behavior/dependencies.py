"""
Dependency Injection + lifecycle cho Behavior module.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request
from loguru import logger

from app.modules.behavior.config import load_behavior_config
from app.modules.behavior.services import BehaviorService, BenchmarkService

_service: Optional[BehaviorService] = None


async def init_behavior_module(app) -> BehaviorService:
    """
    Khởi tạo Behavior Feature Engine khi app startup.

    - Load behavior.yaml.
    - Tạo BehaviorService (nạp pose model nếu auto_load; degrade nếu thiếu deps).
    """
    global _service
    config = load_behavior_config()
    service = BehaviorService(config)
    if config.pose.auto_load:
        service.load_pose()
    _service = service
    app.state.behavior_service = service
    app.state.behavior_config = config
    logger.info(
        "Behavior module initialized (pose_loaded={})", service.pose_loaded
    )
    return service


async def shutdown_behavior_module() -> None:
    """Dọn dẹp khi shutdown."""
    global _service
    if _service is not None:
        _service.shutdown()
    _service = None
    logger.info("Behavior module shutdown complete")


def get_behavior_service(request: Request) -> BehaviorService:
    """FastAPI dependency — BehaviorService từ app.state."""
    service: Optional[BehaviorService] = getattr(
        request.app.state, "behavior_service", None
    )
    if service is None:
        raise RuntimeError("BehaviorService chưa được khởi tạo.")
    return service


def get_behavior_benchmark_service(request: Request) -> BenchmarkService:
    """FastAPI dependency — BenchmarkService behavior."""
    config = getattr(request.app.state, "behavior_config", None)
    if config is None:
        config = load_behavior_config()
    service: Optional[BehaviorService] = getattr(
        request.app.state, "behavior_service", None
    )
    pose = service._pose if service is not None else None  # noqa: SLF001
    return BenchmarkService(config, pose=pose)
