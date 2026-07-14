"""RBAC cho module admin (Sprint 9)."""

from app.modules.admin.rbac.hierarchy import (
    ROLE_ORDER,
    inherited_permissions,
    is_higher_or_equal,
    rank,
)
from app.modules.admin.rbac.permissions import (
    ACTIONS,
    DEFAULT_ROLE_PERMISSIONS,
    MODULES,
    PERMISSION_REGISTRY,
    ROLES,
    PermissionDef,
    expand_permissions,
    has_permission,
    permission_matrix,
)

__all__ = [
    "ACTIONS",
    "MODULES",
    "ROLES",
    "PermissionDef",
    "PERMISSION_REGISTRY",
    "DEFAULT_ROLE_PERMISSIONS",
    "expand_permissions",
    "has_permission",
    "permission_matrix",
    "ROLE_ORDER",
    "rank",
    "is_higher_or_equal",
    "inherited_permissions",
]
