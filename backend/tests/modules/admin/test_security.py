"""Security test — headers, rate limit, auth enforcement (Sprint 9)."""

from __future__ import annotations

import app.middleware.security_middleware as sec
from app.config.settings import get_settings

from .conftest import make_admin_app
from fastapi.testclient import TestClient


def test_security_headers_present():
    client = TestClient(make_admin_app(with_security=True))
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@12345"})
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Request-ID" in resp.headers


def test_rate_limit_returns_429():
    settings = get_settings()
    original = settings.rate_limit_per_minute
    settings.rate_limit_per_minute = 3
    sec._rl_hits.clear()
    try:
        client = TestClient(make_admin_app(with_security=True), raise_server_exceptions=False)
        codes = [
            client.post("/api/v1/auth/login", json={"username": "admin", "password": "x"}).status_code
            for _ in range(6)
        ]
        assert 429 in codes
    finally:
        settings.rate_limit_per_minute = original
        sec._rl_hits.clear()


def test_protected_requires_token():
    client = TestClient(make_admin_app())
    assert client.get("/api/v1/config").status_code == 401
    assert client.get("/api/v1/audit").status_code == 401


def test_sql_injection_like_username_is_safe():
    """Username độc hại chỉ dẫn tới 401, không gây lỗi/execute (repo tham số hoá)."""
    client = TestClient(make_admin_app())
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin' OR '1'='1", "password": "x"},
    )
    assert resp.status_code == 401
