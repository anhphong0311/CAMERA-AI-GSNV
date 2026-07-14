"""User Management Service (Sprint 9) — CRUD user, enable/disable, reset password."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.security import hash_password
from app.exceptions.base import ConflictError, NotFoundError, ValidationError
from app.modules.admin.repositories.base import RoleRepository, UserRepository
from app.modules.admin.repositories.entities import UserEntity
from app.modules.admin.security.password_policy import PasswordPolicy, validate_password


class UserService:
    """Quản lý tài khoản người dùng dashboard."""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        policy: Optional[PasswordPolicy] = None,
    ) -> None:
        self._users = user_repo
        self._roles = role_repo
        self._policy = policy or PasswordPolicy()

    def set_policy(self, policy: PasswordPolicy) -> None:
        self._policy = policy

    def list(self) -> List[UserEntity]:
        return self._users.list()

    def get(self, user_id: str) -> UserEntity:
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError("User", user_id)
        return user

    def _validate_password(self, password: str) -> None:
        result = validate_password(password, self._policy)
        if not result.valid:
            raise ValidationError("; ".join(result.errors))

    def _validate_role(self, role: str) -> None:
        if self._roles.get(role) is None:
            raise ValidationError(f"Role '{role}' không tồn tại.")

    def create(
        self,
        *,
        username: str,
        password: str,
        role: str = "viewer",
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
    ) -> UserEntity:
        if self._users.get_by_username(username) is not None:
            raise ConflictError(f"Username '{username}' đã tồn tại.")
        self._validate_role(role)
        self._validate_password(password)
        user = UserEntity(
            id=uuid.uuid4().hex,
            username=username,
            password_hash=hash_password(password),
            role=role,
            email=email,
            full_name=full_name,
            department=department,
        )
        return self._users.save(user)

    def update(
        self,
        user_id: str,
        *,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
        role: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> UserEntity:
        user = self.get(user_id)
        if role is not None:
            self._validate_role(role)
            user.role = role
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name
        if department is not None:
            user.department = department
        if avatar is not None:
            user.avatar = avatar
        return self._users.save(user)

    def set_active(self, user_id: str, active: bool) -> UserEntity:
        user = self.get(user_id)
        user.is_active = active
        return self._users.save(user)

    def reset_password(self, user_id: str, new_password: str) -> UserEntity:
        user = self.get(user_id)
        self._validate_password(new_password)
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        return self._users.save(user)

    def mark_login(self, user_id: str) -> None:
        user = self._users.get(user_id)
        if user is not None:
            user.last_login_at = datetime.now(timezone.utc)
            self._users.save(user)

    def delete(self, user_id: str) -> None:
        user = self.get(user_id)
        admins = [u for u in self._users.list() if u.role == "admin" and u.is_active]
        if user.role == "admin" and len(admins) <= 1:
            raise ConflictError("Không thể xoá admin cuối cùng của hệ thống.")
        self._users.delete(user_id)
