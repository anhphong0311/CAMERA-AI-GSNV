"""Fixtures cho test module Enterprise Admin (Sprint 9)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin import ADMIN_ROUTERS
from app.exceptions import register_exception_handlers
from app.modules.admin.dependencies import AdminContainer, _build_container


def build_container() -> AdminContainer:
    """Container admin đã seed (roles/config/admin user), KHÔNG start scheduler."""
    return _build_container()


def make_admin_app(with_security: bool = False) -> FastAPI:
    app = FastAPI()
    app.state.admin = build_container()
    register_exception_handlers(app)
    if with_security:
        from app.middleware.security_middleware import register_security_middleware

        register_security_middleware(app)
    for router in ADMIN_ROUTERS:
        app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def container() -> AdminContainer:
    return build_container()


@pytest.fixture
def client() -> TestClient:
    return TestClient(make_admin_app())


@pytest.fixture
def admin_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin@12345"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
