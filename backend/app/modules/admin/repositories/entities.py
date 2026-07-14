"""
Domain entities cho module admin (dataclasses độc lập DB/ORM).

Dùng chung cho repository InMemory (test/default) và ánh xạ sang ORM ở SQL repo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class UserEntity:
    id: str
    username: str
    password_hash: str
    role: str = "viewer"
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = field(default_factory=_now)
    created_at: datetime = field(default_factory=_now)

    def public(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "department": self.department,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RoleEntity:
    name: str
    description: str = ""
    permissions: List[str] = field(default_factory=list)
    system: bool = False  # role hệ thống không được xoá

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "system": self.system,
        }


@dataclass
class AuditEntity:
    action: str
    module: str
    id: Optional[int] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    target: Optional[str] = None
    status: str = "success"
    ip: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "module": self.module,
            "target": self.target,
            "status": self.status,
            "ip": self.ip,
            "detail": self.detail,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ConfigEntity:
    section: str
    key: str
    value: Any = None
    updated_by: Optional[str] = None
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "key": self.key,
            "value": self.value,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ModelEntity:
    name: str
    version: str
    path: str
    id: Optional[int] = None
    status: str = "inactive"
    is_active: bool = False
    metrics: Optional[Dict[str, Any]] = None
    uploaded_by: Optional[str] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "status": self.status,
            "is_active": self.is_active,
            "metrics": self.metrics,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SessionEntity:
    user_id: str
    refresh_jti: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    access_jti: Optional[str] = None
    device: Optional[str] = None
    ip: Optional[str] = None
    last_activity: datetime = field(default_factory=_now)
    expires_at: Optional[datetime] = None
    revoked: bool = False
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device": self.device,
            "ip": self.ip,
            "last_activity": self.last_activity.isoformat(),
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class BackupEntity:
    kind: str
    path: str
    id: Optional[int] = None
    size_bytes: int = 0
    status: str = "completed"
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class JobEntity:
    name: str
    interval_seconds: int = 86400
    enabled: bool = True
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "interval_seconds": self.interval_seconds,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_status": self.last_status,
        }
