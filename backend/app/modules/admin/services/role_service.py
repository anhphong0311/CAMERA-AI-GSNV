"""Role & Permission Management Service (Sprint 9)."""

from __future__ import annotations

from typing import Dict, List

from app.exceptions.base import ConflictError, NotFoundError, ValidationError
from app.modules.admin.rbac import (
    PERMISSION_REGISTRY,
    PermissionDef,
    expand_permissions,
    inherited_permissions,
    permission_matrix,
)
from app.modules.admin.repositories.base import RoleRepository
from app.modules.admin.repositories.entities import RoleEntity


class RoleService:
    """CRUD Role + Permission group + Role hierarchy."""

    def __init__(self, role_repo: RoleRepository) -> None:
        self._roles = role_repo

    def list(self) -> List[RoleEntity]:
        return self._roles.list()

    def get(self, name: str) -> RoleEntity:
        role = self._roles.get(name)
        if role is None:
            raise NotFoundError("Role", name)
        return role

    def _validate_perms(self, permissions: List[str]) -> None:
        for p in permissions:
            if p == "*":
                continue
            if p not in PERMISSION_REGISTRY:
                raise ValidationError(f"Permission '{p}' không hợp lệ.")

    def create(self, name: str, description: str, permissions: List[str]) -> RoleEntity:
        if self._roles.get(name) is not None:
            raise ConflictError(f"Role '{name}' đã tồn tại.")
        self._validate_perms(permissions)
        return self._roles.save(
            RoleEntity(name=name, description=description, permissions=permissions)
        )

    def update(self, name: str, *, description=None, permissions=None) -> RoleEntity:
        role = self.get(name)
        if permissions is not None:
            self._validate_perms(permissions)
            role.permissions = permissions
        if description is not None:
            role.description = description
        return self._roles.save(role)

    def delete(self, name: str) -> None:
        role = self.get(name)
        if role.system:
            raise ConflictError(f"Role hệ thống '{name}' không thể xoá.")
        self._roles.delete(name)

    def effective_permissions(self, name: str) -> List[str]:
        """Quyền hiệu lực (bao gồm kế thừa role hierarchy)."""
        role = self.get(name)
        base = expand_permissions(role.permissions)
        inherited = inherited_permissions(name, {r.name: r.permissions for r in self._roles.list()})
        return sorted(base | inherited)

    @staticmethod
    def registry() -> List[PermissionDef]:
        return list(PERMISSION_REGISTRY.values())

    @staticmethod
    def matrix() -> Dict[str, List[str]]:
        return permission_matrix()
