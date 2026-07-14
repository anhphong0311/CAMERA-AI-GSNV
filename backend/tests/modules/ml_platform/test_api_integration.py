"""API integration tests — ML Platform (Sprint 13)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin import ADMIN_ROUTERS
from app.api.v1.ml_platform import ML_PLATFORM_ROUTERS
from app.exceptions import register_exception_handlers
from app.modules.admin.dependencies import AdminContainer, _build_container
from app.modules.ml_platform.dependencies import _build_container as build_ml


def make_app() -> FastAPI:
    app = FastAPI()
    app.state.admin = _build_container()
    app.state.ml_platform = build_ml(app.state.admin.models)
    register_exception_handlers(app)
    for router in ADMIN_ROUTERS:
        app.include_router(router, prefix="/api/v1")
    for router in ML_PLATFORM_ROUTERS:
        app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(make_app())


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin@12345"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dataset_api_flow(client: TestClient, auth_headers: dict):
    create = client.post(
        "/api/v1/dataset",
        json={"name": "api-ds", "source_type": "event"},
        headers=auth_headers,
    )
    assert create.status_code == 200
    ds_id = create.json()["data"]["id"]

    imp = client.post(
        f"/api/v1/dataset/{ds_id}/import",
        json={"paths": ["/snap1.jpg"]},
        headers=auth_headers,
    )
    assert imp.status_code == 200

    stats = client.get("/api/v1/dataset/statistics", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["data"]["datasets"] >= 1


def test_training_dashboard(client: TestClient, auth_headers: dict):
    resp = client.get("/api/v1/training/dashboard/overview", headers=auth_headers)
    assert resp.status_code == 200
    assert "dataset_stats" in resp.json()["data"]


def test_annotation_labels(client: TestClient, auth_headers: dict):
    resp = client.get("/api/v1/annotation/labels", headers=auth_headers)
    assert resp.status_code == 200
    assert "person" in resp.json()["data"]
