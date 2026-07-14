"""
Role Hierarchy (Sprint 9).

Vai trò cấp cao kế thừa quyền của vai trò cấp thấp hơn:
admin > supervisor > manager > viewer.
"""

from __future__ import annotations

from typing import Dict, List, Set

from app.modules.admin.rbac.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
    expand_permissions,
)

# Thứ tự cấp bậc (cao → thấp)
ROLE_ORDER: List[str] = ["admin", "supervisor", "manager", "viewer"]


def rank(role: str) -> int:
    """Trả về cấp bậc (0 = cao nhất). Role lạ → thấp nhất."""
    return ROLE_ORDER.index(role) if role in ROLE_ORDER else len(ROLE_ORDER)


def is_higher_or_equal(role_a: str, role_b: str) -> bool:
    """role_a có cấp >= role_b không (dùng để giới hạn quản lý user)."""
    return rank(role_a) <= rank(role_b)


def inherited_permissions(
    role: str, matrix: Dict[str, List[str]] | None = None
) -> Set[str]:
    """Quyền hiệu lực của role = quyền của nó + mọi role thấp hơn."""
    matrix = matrix or DEFAULT_ROLE_PERMISSIONS
    if role not in ROLE_ORDER:
        return expand_permissions(matrix.get(role, []))
    result: Set[str] = set()
    idx = ROLE_ORDER.index(role)
    for lower in ROLE_ORDER[idx:]:
        result |= expand_permissions(matrix.get(lower, []))
    return result
