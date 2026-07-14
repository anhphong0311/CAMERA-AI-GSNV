"""Integration test — API Enterprise Admin qua TestClient (JWT + RBAC + CRUD)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_success_and_me(client: TestClient):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@12345"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["user"]["username"] == "admin"
    assert "*" in data["permissions"]

    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["user"]["role"] == "admin"


def test_login_wrong_password(client: TestClient):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_refresh_rotation(client: TestClient):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@12345"}).json()["data"]
    rt = login["refresh_token"]
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert refreshed.status_code == 200
    # refresh token cũ bị thu hồi (rotation)
    again = client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert again.status_code == 401


def test_user_crud_flow(client: TestClient, auth_headers: dict):
    created = client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={"username": "alice", "password": "Str0ng@Pass", "role": "manager"},
    )
    assert created.status_code == 201
    uid = created.json()["data"]["id"]

    listed = client.get("/api/v1/users", headers=auth_headers)
    assert any(u["username"] == "alice" for u in listed.json()["data"])

    updated = client.put(
        f"/api/v1/users/{uid}", headers=auth_headers, json={"department": "Ops"}
    )
    assert updated.json()["data"]["department"] == "Ops"

    disabled = client.post(f"/api/v1/users/{uid}/disable", headers=auth_headers)
    assert disabled.json()["data"]["is_active"] is False

    deleted = client.delete(f"/api/v1/users/{uid}", headers=auth_headers)
    assert deleted.status_code == 200


def test_rbac_viewer_forbidden(client: TestClient, auth_headers: dict):
    client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={"username": "vic", "password": "Str0ng@Pass", "role": "viewer"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"username": "vic", "password": "Str0ng@Pass"}
    ).json()["data"]["access_token"]
    vheaders = {"Authorization": f"Bearer {token}"}
    # viewer không có users:read
    resp = client.get("/api/v1/users", headers=vheaders)
    assert resp.status_code == 403


def test_missing_token_unauthorized(client: TestClient):
    assert client.get("/api/v1/users").status_code == 401


def test_roles_and_permissions(client: TestClient, auth_headers: dict):
    roles = client.get("/api/v1/roles", headers=auth_headers)
    assert roles.status_code == 200
    names = {r["name"] for r in roles.json()["data"]}
    assert {"admin", "supervisor", "manager", "viewer"} <= names

    matrix = client.get("/api/v1/permissions/matrix", headers=auth_headers)
    assert "admin" in matrix.json()["data"]


def test_config_get_set(client: TestClient, auth_headers: dict):
    client.put(
        "/api/v1/config", headers=auth_headers,
        json={"key": "system.company_name", "value": "ACME Corp"},
    )
    section = client.get("/api/v1/config/system", headers=auth_headers)
    assert section.json()["data"]["system.company_name"] == "ACME Corp"


def test_model_lifecycle_api(client: TestClient, auth_headers: dict):
    a = client.post(
        "/api/v1/models", headers=auth_headers,
        json={"name": "yolo", "version": "1.0", "path": "/m/1.pt"},
    ).json()["data"]
    b = client.post(
        "/api/v1/models", headers=auth_headers,
        json={"name": "yolo", "version": "2.0", "path": "/m/2.pt"},
    ).json()["data"]
    client.post(f"/api/v1/models/{b['id']}/switch", headers=auth_headers)
    rollback = client.post("/api/v1/models/yolo/rollback", headers=auth_headers)
    assert rollback.json()["data"]["id"] == a["id"]


def test_scheduler_and_system_health(client: TestClient, auth_headers: dict):
    sched = client.get("/api/v1/scheduler", headers=auth_headers)
    assert sched.status_code == 200
    assert isinstance(sched.json()["data"], list)

    health = client.get("/api/v1/system/health")
    assert health.status_code == 200
    assert health.json()["data"]["status"] in {"healthy", "degraded", "unhealthy"}


def test_audit_records_login(client: TestClient, auth_headers: dict):
    resp = client.get("/api/v1/audit?module=auth", headers=auth_headers)
    assert resp.status_code == 200
    actions = {r["action"] for r in resp.json()["data"]}
    assert "login" in actions
