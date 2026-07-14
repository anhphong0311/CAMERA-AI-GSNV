"""Unit test — RBAC (permissions, matrix, hierarchy)."""

from __future__ import annotations

from app.modules.admin.rbac import (
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_REGISTRY,
    expand_permissions,
    has_permission,
    inherited_permissions,
    is_higher_or_equal,
    permission_matrix,
)


def test_registry_covers_modules_actions():
    assert "users:read" in PERMISSION_REGISTRY
    assert "config:manage" in PERMISSION_REGISTRY


def test_wildcard_grants_all():
    granted = expand_permissions(["*"])
    assert has_permission(granted, "users:delete")
    assert has_permission(["*"], "anything:read")


def test_manage_implies_actions():
    assert has_permission(["cameras:manage"], "cameras:update")
    assert not has_permission(["cameras:read"], "cameras:delete")


def test_admin_matrix_is_full():
    matrix = permission_matrix()
    assert "*" in matrix["admin"]
    assert "cameras:read" in matrix["viewer"]


def test_role_hierarchy():
    assert is_higher_or_equal("admin", "viewer")
    assert not is_higher_or_equal("viewer", "admin")


def test_inherited_permissions_supervisor_includes_viewer():
    perms = inherited_permissions("supervisor", DEFAULT_ROLE_PERMISSIONS)
    # supervisor kế thừa quyền xem của manager/viewer
    assert "cameras:read" in perms
