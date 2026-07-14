"""
Middleware HTTP — logging request/response và CORS.

Tách middleware ra module riêng để main.py gọn (SRP).
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config.settings import get_settings


def register_middleware(app: FastAPI) -> None:
    """
    Đăng ký tất cả middleware lên FastAPI app.

    Args:
        app: Instance FastAPI.
    """
    settings = get_settings()

    # CORS — cho phép frontend gọi API từ origin khác
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Sprint 9 — security headers + rate limit + request-id + /metrics
    from app.middleware.security_middleware import register_security_middleware

    register_security_middleware(app)

    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable
    ) -> Response:
        """
        Ghi log mỗi HTTP request: method, path, status, thời gian xử lý.

        Giúp debug và giám sát hiệu năng API.
        """
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "{method} {path} → {status} ({ms:.1f}ms)",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=elapsed_ms,
        )
        return response
