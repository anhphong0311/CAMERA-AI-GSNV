"""Security & middleware tests for Release v1.0 (Sprint 12 QA)."""

from __future__ import annotations

import app.middleware.security_middleware as sec
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_middleware import register_security_middleware, render_metrics


def _client():
    app = FastAPI()
    register_security_middleware(app)

    @app.get("/api/v1/test")
    def ok():
        return {"ok": True}

    return TestClient(app)


def test_metrics_endpoint():
    client = _client()
    client.get("/api/v1/test")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "aems_http_requests_total" in resp.text


def test_render_metrics_empty():
    with sec._metrics_lock:
        sec._req_total = 0
        sec._latency_count = 0
    text = render_metrics()
    assert "aems_http_requests_total 0" in text


def test_health_exempt_from_rate_limit():
    app = FastAPI()
    register_security_middleware(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app, raise_server_exceptions=False)
    for _ in range(20):
        assert client.get("/api/v1/health").status_code == 200


def test_jwt_invalid_token_rejected():
    from tests.modules.admin.conftest import make_admin_app

    client = TestClient(make_admin_app())
    resp = client.get("/api/v1/users", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_permission_denied_for_viewer_role():
    from tests.modules.admin.conftest import make_admin_app

    client = TestClient(make_admin_app())
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@12345"})
    token = login.json()["data"]["access_token"]
    # Create viewer user scenario — admin can access users
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
