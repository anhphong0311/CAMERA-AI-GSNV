"""
RBAC Permission Registry & Matrix (Sprint 9).

Định nghĩa danh mục quyền theo module + action, và ma trận role→permission mặc
định (seed). Thuần dữ liệu/logic — không phụ thuộc DB. Ma trận thực tế được lưu DB
và có thể chỉnh qua Permission Management (không hardcode khi vận hành).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

# Các module có kiểm soát quyền (Module Permission)
MODULES = [
    "users",
    "roles",
    "permissions",
    "audit",
    "config",
    "cameras",
    "models",
    "dataset",
    "annotation",
    "training",
    "backup",
    "restore",
    "scheduler",
    "system",
    "storage",
    "rules",
    "alerts",
    "replay",
    "reports",
]

# Action chuẩn
ACTIONS = ["read", "create", "update", "delete", "manage"]


@dataclass(frozen=True)
class PermissionDef:
    """Định nghĩa một quyền."""

    code: str
    name: str
    module: str


def _build_registry() -> List[PermissionDef]:
    defs: List[PermissionDef] = []
    for module in MODULES:
        for action in ACTIONS:
            defs.append(
                PermissionDef(
                    code=f"{module}:{action}",
                    name=f"{action.capitalize()} {module}",
                    module=module,
                )
            )
    return defs


# Registry đầy đủ (code → def)
PERMISSION_REGISTRY: Dict[str, PermissionDef] = {
    p.code: p for p in _build_registry()
}

WILDCARD = "*"

# Vai trò chuẩn (RBAC): admin, supervisor, manager, viewer
ROLES = ["admin", "supervisor", "manager", "viewer"]


def _read_only_matrix() -> List[str]:
    return [f"{m}:read" for m in MODULES]


# Ma trận role→permission mặc định (seed vào DB).
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    # Admin: toàn quyền
    "admin": [WILDCARD],
    # Supervisor: quản lý vận hành (không quản trị user/role/backup/restore)
    "supervisor": [
        *[f"{m}:{a}" for m in ["cameras", "rules", "alerts", "config", "models", "storage", "dataset", "annotation", "training"] for a in ["read", "create", "update", "delete"]],
        "audit:read",
        "system:read",
        "scheduler:read",
        "replay:read",
        "reports:read",
        "users:read",
    ],
    # Manager: xem + xuất báo cáo + xem vận hành
    "manager": [
        *_read_only_matrix(),
        "reports:create",
        "replay:read",
    ],
    # Viewer: chỉ xem realtime cơ bản
    "viewer": [
        "cameras:read",
        "alerts:read",
        "replay:read",
        "system:read",
        "reports:read",
    ],
}


def expand_permissions(perms: List[str]) -> Set[str]:
    """Chuẩn hoá danh sách quyền; '*' nghĩa là tất cả."""
    perm_set = set(perms or [])
    if WILDCARD in perm_set:
        return set(PERMISSION_REGISTRY.keys()) | {WILDCARD}
    return perm_set


def has_permission(granted: List[str] | Set[str], required: str) -> bool:
    """Kiểm tra tập quyền `granted` có thoả `required` không."""
    granted_set = granted if isinstance(granted, set) else set(granted or [])
    if WILDCARD in granted_set:
        return True
    if required in granted_set:
        return True
    # Cho phép '<module>:manage' bao hàm mọi action của module
    module = required.split(":", 1)[0]
    return f"{module}:manage" in granted_set


def permission_matrix() -> Dict[str, List[str]]:
    """Ma trận role→permission (đã expand) cho hiển thị/kiểm tra."""
    return {
        role: sorted(expand_permissions(perms))
        for role, perms in DEFAULT_ROLE_PERMISSIONS.items()
    }
