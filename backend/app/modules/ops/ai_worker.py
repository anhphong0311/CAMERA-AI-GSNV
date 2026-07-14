"""
AI Worker entrypoint (Sprint 11) — chạy pipeline AI/Camera không qua Uvicorn.

Dùng trong container `ai-worker` hoặc systemd service riêng.
Không thay đổi logic Detection/Tracking — chỉ khởi tạo module và giữ process sống.
"""

from __future__ import annotations

import asyncio
import signal
import sys

from loguru import logger


async def _run() -> None:
    from app.config.settings import get_settings
    from app.core.database import close_db, init_db
    from app.core.logging import setup_logging
    from app.core.redis import close_redis, init_redis
    from app.modules.ai.dependencies import init_ai_module, shutdown_ai_module
    from app.modules.camera.dependencies import init_camera_module, shutdown_camera_module
    from app.modules.performance.dependencies import init_performance_module, shutdown_performance_module

    settings = get_settings()
    setup_logging()
    logger.info("AI Worker starting | env={}", settings.environment)

    init_db()
    await init_redis()

    # Minimal FastAPI-like state object
    class _State:
        pass

    class _App:
        state = _State()

    app = _App()
    await init_camera_module(app)
    await init_ai_module(app)
    await init_performance_module(app)

    logger.info("AI Worker modules ready — pipeline running")

    stop = asyncio.Event()

    def _signal_handler(*_):
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop.set())

    await stop.wait()

    await shutdown_performance_module(app)
    await shutdown_ai_module()
    await shutdown_camera_module()
    await close_redis()
    await close_db()
    logger.info("AI Worker shutdown complete")


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
