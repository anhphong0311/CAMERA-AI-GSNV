"""
Middleware bảo mật & giám sát (Sprint 9).

- Request-ID cho mỗi request (truy vết log).
- Security headers (XSS/Content-Type/Frame/HSTS).
- Rate limiting (fixed-window theo IP) — chống lạm dụng/brute force.
- API metrics + endpoint Prometheus /metrics.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config.settings import get_settings

# ---- API metrics (thread-safe, đơn giản, không cần prometheus_client) ----
_metrics_lock = threading.Lock()
_req_total = 0
_req_by_status: Dict[str, int] = defaultdict(int)
_req_by_method: Dict[str, int] = defaultdict(int)
_latency_sum = 0.0
_latency_count = 0

# ---- Rate limiting state ----
_rl_lock = threading.Lock()
_rl_hits: Dict[Tuple[str, int], int] = defaultdict(int)

# Đường dẫn miễn rate-limit / không tính là API nghiệp vụ
_EXEMPT_PREFIXES = ("/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi", "/metrics", "/api/v1/health")


def _record(method: str, status_code: int, elapsed: float) -> None:
    global _req_total, _latency_sum, _latency_count
    with _metrics_lock:
        _req_total += 1
        _req_by_method[method] += 1
        _req_by_status[f"{status_code // 100}xx"] += 1
        _latency_sum += elapsed
        _latency_count += 1


def _rate_limited(ip: str, limit: int) -> bool:
    window = int(time.time() // 60)
    key = (ip, window)
    with _rl_lock:
        # dọn cửa sổ cũ
        for k in [k for k in _rl_hits if k[1] != window]:
            _rl_hits.pop(k, None)
        _rl_hits[key] += 1
        return _rl_hits[key] > limit


def render_metrics() -> str:
    with _metrics_lock:
        lines = [
            "# HELP aems_http_requests_total Total HTTP requests",
            "# TYPE aems_http_requests_total counter",
            f"aems_http_requests_total {_req_total}",
            "# HELP aems_http_request_latency_seconds_avg Average request latency",
            "# TYPE aems_http_request_latency_seconds_avg gauge",
            f"aems_http_request_latency_seconds_avg {(_latency_sum / _latency_count) if _latency_count else 0.0:.6f}",
        ]
        for status, count in sorted(_req_by_status.items()):
            lines.append(f'aems_http_requests_status{{class="{status}"}} {count}')
        for method, count in sorted(_req_by_method.items()):
            lines.append(f'aems_http_requests_method{{method="{method}"}} {count}')
    return "\n".join(lines) + "\n"


def register_security_middleware(app: FastAPI) -> None:
    settings = get_settings()

    @app.middleware("http")
    async def security_and_metrics(request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id", uuid.uuid4().hex)
        path = request.url.path

        # Rate limit (bỏ qua path exempt)
        if not any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            ip = request.client.host if request.client else "unknown"
            if _rate_limited(ip, settings.rate_limit_per_minute):
                return JSONResponse(
                    status_code=429,
                    content={"data": None, "error": {"code": "RATE_LIMITED", "message": "Quá nhiều yêu cầu."}},
                    headers={"X-Request-ID": request_id, "Retry-After": "60"},
                )

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        _record(request.method, response.status_code, elapsed)

        # Security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.is_development:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    if settings.enable_metrics:

        @app.get("/metrics", include_in_schema=False)
        async def metrics() -> PlainTextResponse:
            return PlainTextResponse(render_metrics(), media_type="text/plain; version=0.0.4")
