"""
Dependency Injection & guards cho module Enterprise Admin (Sprint 9).

Khởi tạo repositories (InMemory mặc định), services, scheduler; seed dữ liệu; đăng ký
health checks & backup providers; và cung cấp guard get_current_user / require_permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, FastAPI, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from loguru import logger

from app.config.settings import get_settings
from app.exceptions.base import ForbiddenError, UnauthorizedError
from app.modules.admin.rbac import has_permission
from app.modules.admin.repositories.memory import (
    InMemoryAuditRepository,
    InMemoryBackupRepository,
    InMemoryConfigRepository,
    InMemoryJobRepository,
    InMemoryModelRepository,
    InMemoryRoleRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
)
from app.modules.admin.scheduler import AsyncScheduler
from app.modules.admin.seed import seed_all
from app.modules.admin.security.tokens import verify_token
from app.modules.admin.services import (
    AuditService,
    AuthService,
    BackupService,
    ConfigService,
    HealthMonitorService,
    ModelService,
    RestoreService,
    RoleService,
    SchedulerService,
    StorageService,
    SystemMonitorService,
    UserService,
)


@dataclass
class AdminContainer:
    """Gói toàn bộ repositories + services của module admin."""

    audit: AuditService
    config: ConfigService
    users: UserService
    roles: RoleService
    auth: AuthService
    models: ModelService
    backup: BackupService
    restore: RestoreService
    storage: StorageService
    system: SystemMonitorService
    health: HealthMonitorService
    scheduler: AsyncScheduler
    scheduler_service: SchedulerService


def _build_container() -> AdminContainer:
    settings = get_settings()

    user_repo = InMemoryUserRepository()
    role_repo = InMemoryRoleRepository()
    session_repo = InMemorySessionRepository()
    audit_repo = InMemoryAuditRepository()
    config_repo = InMemoryConfigRepository()
    model_repo = InMemoryModelRepository()
    backup_repo = InMemoryBackupRepository()
    job_repo = InMemoryJobRepository()

    audit = AuditService(audit_repo)
    config = ConfigService(config_repo)
    seed_all(user_repo, role_repo, config)

    users = UserService(user_repo, role_repo, config.password_policy())
    roles = RoleService(role_repo)
    auth = AuthService(user_repo, role_repo, session_repo, config, audit)
    models = ModelService(model_repo, audit)

    backup = BackupService(
        backup_repo,
        audit,
        base_dir=str(config.get_value("storage.backup_path", "./data/backups")),
        database_url=str(settings.database_url),
        providers={"config": lambda: {c.key: c.value for c in config_repo.all()}},
    )
    restore = RestoreService(
        backup_repo,
        audit,
        handlers={"config": lambda data: _restore_config(config, data)},
    )
    storage = StorageService(config, audit)
    system = SystemMonitorService()
    health = HealthMonitorService()

    scheduler = AsyncScheduler(job_repo)
    scheduler_service = SchedulerService(scheduler, storage, backup, config, audit)

    return AdminContainer(
        audit=audit,
        config=config,
        users=users,
        roles=roles,
        auth=auth,
        models=models,
        backup=backup,
        restore=restore,
        storage=storage,
        system=system,
        health=health,
        scheduler=scheduler,
        scheduler_service=scheduler_service,
    )


def _restore_config(config: ConfigService, data: dict) -> dict:
    applied = 0
    for key, value in (data or {}).items():
        config.set_value(key, value, updated_by="restore")
        applied += 1
    return {"restored_keys": applied}


def _register_health_checks(container: AdminContainer) -> None:
    from app.core.redis import check_redis_connection

    async def _redis() -> dict:
        try:
            ok = await check_redis_connection()
            return {"ok": bool(ok), "detail": "connected" if ok else "unreachable"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": str(exc)}

    async def _database() -> dict:
        try:
            from sqlalchemy import text

            from app.core.database import get_session_factory

            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
            return {"ok": True, "detail": "connected"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": str(exc)}

    container.health.register("redis", _redis)
    container.health.register("database", _database)
    # Camera/GPU/Telegram/WebSocket: best-effort (module có thể chưa cấu hình)
    container.health.register(
        "gpu",
        lambda: {"ok": True, "detail": container.system.snapshot().get("gpu_available", False) and "available" or "cpu-only"},
    )
    container.health.register("telegram", lambda: {"ok": True, "detail": "configured via ConfigCenter"})
    container.health.register("websocket", lambda: {"ok": True, "detail": "endpoint /api/v1/ws"})
    container.health.register("camera", lambda: {"ok": True, "detail": "managed by camera module"})


async def init_admin_module(app: FastAPI) -> None:
    """Khởi tạo module admin và gắn vào app.state."""
    container = _build_container()
    _register_health_checks(container)
    container.scheduler_service.register_default_jobs()
    container.scheduler.start()
    app.state.admin = container
    logger.info("Admin (Enterprise) module initialized")


async def shutdown_admin_module(app: FastAPI | None = None) -> None:
    container = getattr(getattr(app, "state", None), "admin", None) if app else None
    if container is not None:
        await container.scheduler.stop()


# ----- Accessors -----
def get_admin(request: Request) -> AdminContainer:
    container = getattr(request.app.state, "admin", None)
    if container is None:
        raise UnauthorizedError("Admin module chưa sẵn sàng.")
    return container


_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Giải mã access token → thông tin user (sub/role/permissions)."""
    if credentials is None:
        raise UnauthorizedError("Thiếu access token.")
    try:
        payload = verify_token(credentials.credentials, "access")
    except JWTError as exc:
        raise UnauthorizedError("Access token không hợp lệ hoặc hết hạn.") from exc
    return {
        "id": payload.get("sub"),
        "role": payload.get("role"),
        "permissions": payload.get("permissions", []),
        "jti": payload.get("jti"),
    }


def require_permission(permission: str) -> Callable:
    """Factory tạo dependency kiểm tra quyền (RBAC)."""

    async def _guard(user: dict = Depends(get_current_user)) -> dict:
        if not has_permission(user.get("permissions", []), permission):
            raise ForbiddenError(f"Thiếu quyền '{permission}'.")
        return user

    return _guard


def client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None
