"""Repository layer cho module admin."""

from app.modules.admin.repositories.base import (
    AuditRepository,
    BackupRepository,
    ConfigRepository,
    JobRepository,
    ModelRepository,
    RoleRepository,
    SessionRepository,
    UserRepository,
)
from app.modules.admin.repositories.entities import (
    AuditEntity,
    BackupEntity,
    ConfigEntity,
    JobEntity,
    ModelEntity,
    RoleEntity,
    SessionEntity,
    UserEntity,
)
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

__all__ = [
    "UserRepository",
    "RoleRepository",
    "AuditRepository",
    "ConfigRepository",
    "ModelRepository",
    "SessionRepository",
    "BackupRepository",
    "JobRepository",
    "UserEntity",
    "RoleEntity",
    "AuditEntity",
    "ConfigEntity",
    "ModelEntity",
    "SessionEntity",
    "BackupEntity",
    "JobEntity",
    "InMemoryUserRepository",
    "InMemoryRoleRepository",
    "InMemoryAuditRepository",
    "InMemoryConfigRepository",
    "InMemoryModelRepository",
    "InMemorySessionRepository",
    "InMemoryBackupRepository",
    "InMemoryJobRepository",
]
