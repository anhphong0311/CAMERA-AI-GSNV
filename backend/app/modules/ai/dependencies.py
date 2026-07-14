"""
Dependency Injection + lifecycle cho AI Detection module.

Khởi tạo DetectionService khi app startup (auto_load tùy config, có bọc
try/except để không crash app khi thiếu weight/torch).
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request
from loguru import logger

from app.modules.ai.config import load_detection_config
from app.modules.ai.services.benchmark_service import BenchmarkService
from app.modules.ai.services.detection_service import DetectionService

# Singleton service — gắn vào app.state
_service: Optional[DetectionService] = None


async def init_ai_module(app) -> DetectionService:
    """
    Khởi tạo Detection Engine khi app startup.

    - Load config detection.yaml.
    - Tạo DetectionService.
    - Nếu auto_load: thử load + warmup model (bọc try/except để không crash
      app khi chưa có weight/torch trong môi trường hiện tại).
    - Khởi động pipeline đa camera.

    Args:
        app: FastAPI application.

    Returns:
        DetectionService.
    """
    global _service
    config = load_detection_config()
    try:
        from app.modules.performance.config import load_performance_config

        perf_config = load_performance_config()
    except Exception:
        perf_config = None
    _service = DetectionService(config, perf_config)
    app.state.ai_service = _service
    app.state.ai_config = config

    if config.auto_load:
        try:
            info = _service.load_model()
            logger.info("AI model loaded on startup | {}", info.name)
        except Exception as exc:
            logger.warning(
                "AI model auto-load bỏ qua (sẽ load khi reload): {}", exc
            )

    _service.start_pipeline()
    logger.info("AI Detection module initialized")
    return _service


async def shutdown_ai_module() -> None:
    """Dừng pipeline và giải phóng model khi shutdown."""
    global _service
    if _service is not None:
        _service.stop_pipeline()
        _service.release_model()
        _service = None
        logger.info("AI Detection module shutdown complete")


def get_detection_service(request: Request) -> DetectionService:
    """
    FastAPI dependency — lấy DetectionService từ app.state.

    Raises:
        RuntimeError: Module chưa khởi tạo.
    """
    service: Optional[DetectionService] = getattr(
        request.app.state, "ai_service", None
    )
    if service is None:
        raise RuntimeError("DetectionService chưa được khởi tạo.")
    return service


def get_benchmark_service(request: Request) -> BenchmarkService:
    """FastAPI dependency — BenchmarkService bọc DetectionService."""
    return BenchmarkService(get_detection_service(request))
