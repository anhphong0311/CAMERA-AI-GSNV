"""
Seed dữ liệu khởi tạo cho module admin (Sprint 9).

Seed role hệ thống (admin/supervisor/manager/viewer), config mặc định và tài khoản
admin đầu tiên (thông tin lấy từ settings/env — không hardcode trong logic).
"""

from __future__ import annotations

import uuid

from loguru import logger

from app.config.settings import get_settings
from app.core.security import hash_password
from app.modules.admin.rbac import DEFAULT_ROLE_PERMISSIONS
from app.modules.admin.repositories.base import RoleRepository, UserRepository
from app.modules.admin.repositories.entities import RoleEntity, UserEntity
from app.modules.admin.services.config_service import ConfigService

_ROLE_DESCRIPTIONS = {
    "admin": "Toàn quyền quản trị hệ thống",
    "supervisor": "Giám sát vận hành camera/rule/alert",
    "manager": "Xem báo cáo và dữ liệu vận hành",
    "viewer": "Chỉ xem realtime cơ bản",
}


def seed_roles(role_repo: RoleRepository) -> None:
    for name, perms in DEFAULT_ROLE_PERMISSIONS.items():
        if role_repo.get(name) is None:
            role_repo.save(
                RoleEntity(
                    name=name,
                    description=_ROLE_DESCRIPTIONS.get(name, ""),
                    permissions=list(perms),
                    system=True,
                )
            )


def seed_admin_user(user_repo: UserRepository) -> None:
    settings = get_settings()
    if user_repo.get_by_username(settings.admin_username) is not None:
        return
    user_repo.save(
        UserEntity(
            id=uuid.uuid4().hex,
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            role="admin",
            email=settings.admin_email,
            full_name="System Administrator",
            department="IT",
        )
    )
    logger.info("Seeded admin user '{}'", settings.admin_username)


def seed_all(
    user_repo: UserRepository,
    role_repo: RoleRepository,
    config: ConfigService,
) -> None:
    seed_roles(role_repo)
    config.seed_defaults()
    seed_admin_user(user_repo)
