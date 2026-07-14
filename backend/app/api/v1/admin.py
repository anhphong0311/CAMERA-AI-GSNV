"""
API Enterprise Admin (Sprint 9).

Gồm các router: auth, users, roles, permissions, audit, config, system, storage,
models, backup, restore, scheduler. Bảo vệ bằng RBAC (require_permission).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request

from app.modules.admin.dependencies import (
    AdminContainer,
    client_ip,
    get_admin,
    get_current_user,
    require_permission,
)
from app.modules.admin.schemas import (
    BackupCreateBody,
    ConfigSetBody,
    JobToggleBody,
    LoginBody,
    ModelBenchmarkBody,
    ModelRegisterBody,
    RefreshBody,
    ResetPasswordBody,
    RoleCreateBody,
    RoleUpdateBody,
    UserCreateBody,
    UserUpdateBody,
)
from app.schemas.common import ApiResponse, MessageResponse

# ===================== AUTH =====================
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/login", response_model=ApiResponse[dict])
async def login(
    body: LoginBody, request: Request, admin: AdminContainer = Depends(get_admin)
) -> ApiResponse[dict]:
    data = admin.auth.login(
        body.username, body.password, remember=body.remember, ip=client_ip(request),
        device=request.headers.get("user-agent"),
    )
    return ApiResponse(data=data)


@auth_router.post("/refresh", response_model=ApiResponse[dict])
async def refresh(
    body: RefreshBody, request: Request, admin: AdminContainer = Depends(get_admin)
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.auth.refresh(body.refresh_token, ip=client_ip(request)))


@auth_router.post("/logout", response_model=ApiResponse[MessageResponse])
async def logout(
    body: RefreshBody, request: Request, admin: AdminContainer = Depends(get_admin)
) -> ApiResponse[MessageResponse]:
    admin.auth.logout(body.refresh_token, ip=client_ip(request))
    return ApiResponse(data=MessageResponse(message="Đã đăng xuất."))


@auth_router.post("/logout-all", response_model=ApiResponse[dict])
async def logout_all(
    request: Request,
    admin: AdminContainer = Depends(get_admin),
    user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    count = admin.auth.logout_all(user["id"], ip=client_ip(request))
    return ApiResponse(data={"revoked": count})


@auth_router.get("/me", response_model=ApiResponse[dict])
async def me(
    admin: AdminContainer = Depends(get_admin), user: dict = Depends(get_current_user)
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.auth.me(user["id"]))


@auth_router.get("/sessions", response_model=ApiResponse[list])
async def sessions(
    admin: AdminContainer = Depends(get_admin), user: dict = Depends(get_current_user)
) -> ApiResponse[list]:
    return ApiResponse(data=admin.auth.sessions(user["id"]))


# ===================== USERS =====================
users_router = APIRouter(prefix="/users", tags=["User Management"])


@users_router.get("", response_model=ApiResponse[list])
async def list_users(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("users:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[u.public() for u in admin.users.list()])


@users_router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_user(
    body: UserCreateBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:create")),
) -> ApiResponse[dict]:
    user = admin.users.create(
        username=body.username, password=body.password, role=body.role,
        email=body.email, full_name=body.full_name, department=body.department,
    )
    admin.audit.log("create", "users", user_id=actor["id"], target=body.username)
    return ApiResponse(data=user.public())


@users_router.get("/{user_id}", response_model=ApiResponse[dict])
async def get_user(
    user_id: str,
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("users:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.users.get(user_id).public())


@users_router.put("/{user_id}", response_model=ApiResponse[dict])
async def update_user(
    user_id: str,
    body: UserUpdateBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:update")),
) -> ApiResponse[dict]:
    user = admin.users.update(
        user_id, email=body.email, full_name=body.full_name,
        department=body.department, role=body.role, avatar=body.avatar,
    )
    admin.audit.log("update", "users", user_id=actor["id"], target=user_id)
    return ApiResponse(data=user.public())


@users_router.delete("/{user_id}", response_model=ApiResponse[MessageResponse])
async def delete_user(
    user_id: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:delete")),
) -> ApiResponse[MessageResponse]:
    admin.users.delete(user_id)
    admin.audit.log("delete", "users", user_id=actor["id"], target=user_id)
    return ApiResponse(data=MessageResponse(message="Đã xoá user."))


@users_router.post("/{user_id}/enable", response_model=ApiResponse[dict])
async def enable_user(
    user_id: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:update")),
) -> ApiResponse[dict]:
    user = admin.users.set_active(user_id, True)
    admin.audit.log("enable", "users", user_id=actor["id"], target=user_id)
    return ApiResponse(data=user.public())


@users_router.post("/{user_id}/disable", response_model=ApiResponse[dict])
async def disable_user(
    user_id: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:update")),
) -> ApiResponse[dict]:
    user = admin.users.set_active(user_id, False)
    admin.auth.logout_all(user_id)
    admin.audit.log("disable", "users", user_id=actor["id"], target=user_id)
    return ApiResponse(data=user.public())


@users_router.post("/{user_id}/reset-password", response_model=ApiResponse[MessageResponse])
async def reset_password(
    user_id: str,
    body: ResetPasswordBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:update")),
) -> ApiResponse[MessageResponse]:
    admin.users.reset_password(user_id, body.new_password)
    admin.auth.logout_all(user_id)
    admin.audit.log("reset_password", "users", user_id=actor["id"], target=user_id)
    return ApiResponse(data=MessageResponse(message="Đã đặt lại mật khẩu."))


@users_router.post("/{user_id}/force-logout", response_model=ApiResponse[dict])
async def force_logout(
    user_id: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("users:update")),
) -> ApiResponse[dict]:
    count = admin.auth.logout_all(user_id)
    admin.audit.log("force_logout", "users", user_id=actor["id"], target=user_id)
    return ApiResponse(data={"revoked": count})


# ===================== ROLES =====================
roles_router = APIRouter(prefix="/roles", tags=["Role Management"])


@roles_router.get("", response_model=ApiResponse[list])
async def list_roles(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("roles:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[r.to_dict() for r in admin.roles.list()])


@roles_router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_role(
    body: RoleCreateBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("roles:create")),
) -> ApiResponse[dict]:
    role = admin.roles.create(body.name, body.description, body.permissions)
    admin.audit.log("create", "roles", user_id=actor["id"], target=body.name)
    return ApiResponse(data=role.to_dict())


@roles_router.get("/{name}", response_model=ApiResponse[dict])
async def get_role(
    name: str,
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("roles:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.roles.get(name).to_dict())


@roles_router.put("/{name}", response_model=ApiResponse[dict])
async def update_role(
    name: str,
    body: RoleUpdateBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("roles:update")),
) -> ApiResponse[dict]:
    role = admin.roles.update(name, description=body.description, permissions=body.permissions)
    admin.audit.log("update", "roles", user_id=actor["id"], target=name)
    return ApiResponse(data=role.to_dict())


@roles_router.delete("/{name}", response_model=ApiResponse[MessageResponse])
async def delete_role(
    name: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("roles:delete")),
) -> ApiResponse[MessageResponse]:
    admin.roles.delete(name)
    admin.audit.log("delete", "roles", user_id=actor["id"], target=name)
    return ApiResponse(data=MessageResponse(message="Đã xoá role."))


@roles_router.get("/{name}/effective-permissions", response_model=ApiResponse[list])
async def effective_permissions(
    name: str,
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("roles:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=admin.roles.effective_permissions(name))


# ===================== PERMISSIONS =====================
permissions_router = APIRouter(prefix="/permissions", tags=["Permission Management"])


@permissions_router.get("", response_model=ApiResponse[list])
async def list_permissions(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("permissions:read")),
) -> ApiResponse[list]:
    return ApiResponse(
        data=[{"code": p.code, "name": p.name, "module": p.module} for p in admin.roles.registry()]
    )


@permissions_router.get("/matrix", response_model=ApiResponse[dict])
async def permission_matrix(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("permissions:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.roles.matrix())


# ===================== AUDIT =====================
audit_router = APIRouter(prefix="/audit", tags=["Audit Center"])


@audit_router.get("", response_model=ApiResponse[list])
async def query_audit(
    action: Optional[str] = None,
    module: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("audit:read")),
) -> ApiResponse[list]:
    rows = admin.audit.query(action=action, module=module, user_id=user_id, limit=limit)
    return ApiResponse(data=[r.to_dict() for r in rows], meta={"total": len(rows)})


# ===================== CONFIG =====================
config_router = APIRouter(prefix="/config", tags=["Configuration Center"])


@config_router.get("", response_model=ApiResponse[list])
async def list_config(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("config:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=admin.config.all())


@config_router.get("/{section}", response_model=ApiResponse[dict])
async def get_config_section(
    section: str,
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("config:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.config.get_section(section))


@config_router.put("", response_model=ApiResponse[dict])
async def set_config(
    body: ConfigSetBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("config:update")),
) -> ApiResponse[dict]:
    entry = admin.config.set_value(body.key, body.value, updated_by=actor["id"])
    admin.audit.log("update", "config", user_id=actor["id"], target=body.key)
    # Cập nhật lại password policy cho UserService khi thay đổi
    admin.users.set_policy(admin.config.password_policy())
    return ApiResponse(data=entry.to_dict())


@config_router.delete("/{key}", response_model=ApiResponse[MessageResponse])
async def delete_config(
    key: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("config:update")),
) -> ApiResponse[MessageResponse]:
    admin.config.delete(key)
    admin.audit.log("delete", "config", user_id=actor["id"], target=key)
    return ApiResponse(data=MessageResponse(message="Đã xoá cấu hình."))


# ===================== SYSTEM MONITOR + HEALTH =====================
system_router = APIRouter(prefix="/system", tags=["System Monitor"])


@system_router.get("/metrics", response_model=ApiResponse[dict])
async def system_metrics(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.system.snapshot())


@system_router.get("/health", response_model=ApiResponse[dict])
async def system_health(admin: AdminContainer = Depends(get_admin)) -> ApiResponse[dict]:
    return ApiResponse(data=await admin.health.check_all())


@system_router.get("/info", response_model=ApiResponse[dict])
async def system_info(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[dict]:
    return ApiResponse(
        data={
            "company_name": admin.config.get_value("system.company_name"),
            "office_name": admin.config.get_value("system.office_name"),
            "timezone": admin.config.get_value("system.timezone"),
            "language": admin.config.get_value("system.language"),
            "version": "9.0.0-sprint9",
        }
    )


# ===================== STORAGE =====================
storage_router = APIRouter(prefix="/storage", tags=["Storage Management"])


@storage_router.get("/usage", response_model=ApiResponse[dict])
async def storage_usage(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("storage:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.storage.disk_usage())


@storage_router.get("/retention", response_model=ApiResponse[dict])
async def storage_retention(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("storage:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.storage.retention())


@storage_router.post("/cleanup", response_model=ApiResponse[dict])
async def storage_cleanup(
    kind: Optional[str] = None,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("storage:manage")),
) -> ApiResponse[dict]:
    if kind:
        return ApiResponse(data=admin.storage.cleanup(kind, actor=actor["id"]))
    return ApiResponse(data=admin.storage.cleanup_all(actor=actor["id"]))


# ===================== AI MODELS =====================
models_router = APIRouter(prefix="/models", tags=["AI Model Management"])


@models_router.get("", response_model=ApiResponse[list])
async def list_models(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("models:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[m.to_dict() for m in admin.models.list()])


@models_router.get("/status", response_model=ApiResponse[dict])
async def models_status(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("models:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.models.status())


@models_router.post("", response_model=ApiResponse[dict], status_code=201)
async def register_model(
    body: ModelRegisterBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("models:create")),
) -> ApiResponse[dict]:
    model = admin.models.register(
        name=body.name, version=body.version, path=body.path,
        uploaded_by=actor["id"], metrics=body.metrics,
    )
    return ApiResponse(data=model.to_dict())


@models_router.post("/{model_id}/switch", response_model=ApiResponse[dict])
async def switch_model(
    model_id: int,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.models.switch(model_id, actor=actor["id"]).to_dict())


@models_router.post("/{name}/rollback", response_model=ApiResponse[dict])
async def rollback_model(
    name: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.models.rollback(name, actor=actor["id"]).to_dict())


@models_router.post("/{model_id}/benchmark", response_model=ApiResponse[dict])
async def benchmark_model(
    model_id: int,
    body: ModelBenchmarkBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.models.benchmark(model_id, body.metrics, actor=actor["id"]).to_dict())


@models_router.delete("/{model_id}", response_model=ApiResponse[MessageResponse])
async def delete_model(
    model_id: int,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("models:delete")),
) -> ApiResponse[MessageResponse]:
    admin.models.delete(model_id, actor=actor["id"])
    return ApiResponse(data=MessageResponse(message="Đã xoá model."))


# ===================== BACKUP =====================
backup_router = APIRouter(prefix="/backup", tags=["Backup"])


@backup_router.get("", response_model=ApiResponse[list])
async def list_backups(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("backup:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[b.to_dict() for b in admin.backup.list()])


@backup_router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_backup(
    body: BackupCreateBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("backup:create")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.backup.create_backup(body.kind, actor=actor["id"]).to_dict())


@backup_router.get("/{backup_id}", response_model=ApiResponse[dict])
async def get_backup(
    backup_id: int,
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("backup:read")),
) -> ApiResponse[dict]:
    record = admin.backup.get(backup_id)
    if record is None:
        return ApiResponse(error={"code": "NOT_FOUND", "message": "Backup không tồn tại."})
    return ApiResponse(data=record.to_dict())


# ===================== RESTORE =====================
restore_router = APIRouter(prefix="/restore", tags=["Restore"])


@restore_router.post("/{backup_id}", response_model=ApiResponse[dict])
async def restore_backup(
    backup_id: int,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("restore:create")),
) -> ApiResponse[dict]:
    return ApiResponse(data=admin.restore.restore(backup_id, actor=actor["id"]))


# ===================== SCHEDULER =====================
scheduler_router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@scheduler_router.get("", response_model=ApiResponse[list])
async def scheduler_status(
    admin: AdminContainer = Depends(get_admin),
    _: dict = Depends(require_permission("scheduler:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=admin.scheduler_service.status())


@scheduler_router.post("/{name}/run", response_model=ApiResponse[MessageResponse])
async def run_job(
    name: str,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("scheduler:manage")),
) -> ApiResponse[MessageResponse]:
    await admin.scheduler_service.run_now(name)
    admin.audit.log("run", "scheduler", user_id=actor["id"], target=name)
    return ApiResponse(data=MessageResponse(message=f"Đã chạy job '{name}'."))


@scheduler_router.post("/{name}/toggle", response_model=ApiResponse[dict])
async def toggle_job(
    name: str,
    body: JobToggleBody,
    admin: AdminContainer = Depends(get_admin),
    actor: dict = Depends(require_permission("scheduler:manage")),
) -> ApiResponse[dict]:
    ok = admin.scheduler_service.set_enabled(name, body.enabled, actor=actor["id"])
    return ApiResponse(data={"name": name, "enabled": body.enabled, "updated": ok})


ADMIN_ROUTERS = [
    auth_router,
    users_router,
    roles_router,
    permissions_router,
    audit_router,
    config_router,
    system_router,
    storage_router,
    models_router,
    backup_router,
    restore_router,
    scheduler_router,
]
