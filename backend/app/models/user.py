"""
ORM model: roles, permissions, role_permissions, users.

RBAC — Role-Based Access Control:
- permissions: quyền chi tiết (code machine-readable).
- roles: nhóm quyền (admin, hr, manager, auditor).
- role_permissions: bảng nối M:N.
- users: tài khoản đăng nhập gắn 1 role.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.employee import Employee


class Permission(Base, TimestampMixin):
    """
    Quyền hạn chi tiết trong hệ thống.

    Ví dụ: cameras:read, alerts:write, rules:manage.
    """

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[List["Role"]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
    )


class Role(Base, TimestampMixin):
    """
    Vai trò người dùng — gom nhiều permission.

    Sprint 1 seed: admin, hr, manager, auditor.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
    )
    users: Mapped[List["User"]] = relationship(back_populates="role")


class RolePermission(Base):
    """
    Bảng nối M:N giữa roles và permissions.

    Không kế thừa TimestampMixin vì là bảng junction thuần.
    """

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )


class User(Base, TimestampMixin):
    """
    Tài khoản đăng nhập hệ thống (admin, HR, manager...).

    Khác với employees — user là người dùng dashboard, không nhất thiết là nhân viên được giám sát.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    role: Mapped["Role | None"] = relationship(back_populates="users")
