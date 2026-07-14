"""
Repository ABCs cho module admin (Sprint 9).

Service chỉ phụ thuộc interface — có thể swap InMemory (test/default) ↔ SQL (prod).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

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


class UserRepository(ABC):
    @abstractmethod
    def list(self) -> List[UserEntity]: ...
    @abstractmethod
    def get(self, user_id: str) -> Optional[UserEntity]: ...
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[UserEntity]: ...
    @abstractmethod
    def save(self, user: UserEntity) -> UserEntity: ...
    @abstractmethod
    def delete(self, user_id: str) -> bool: ...


class RoleRepository(ABC):
    @abstractmethod
    def list(self) -> List[RoleEntity]: ...
    @abstractmethod
    def get(self, name: str) -> Optional[RoleEntity]: ...
    @abstractmethod
    def save(self, role: RoleEntity) -> RoleEntity: ...
    @abstractmethod
    def delete(self, name: str) -> bool: ...


class AuditRepository(ABC):
    @abstractmethod
    def add(self, entry: AuditEntity) -> AuditEntity: ...
    @abstractmethod
    def query(
        self,
        *,
        action: Optional[str] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntity]: ...


class ConfigRepository(ABC):
    @abstractmethod
    def all(self) -> List[ConfigEntity]: ...
    @abstractmethod
    def get(self, key: str) -> Optional[ConfigEntity]: ...
    @abstractmethod
    def section(self, section: str) -> List[ConfigEntity]: ...
    @abstractmethod
    def set(self, entry: ConfigEntity) -> ConfigEntity: ...
    @abstractmethod
    def delete(self, key: str) -> bool: ...


class ModelRepository(ABC):
    @abstractmethod
    def list(self) -> List[ModelEntity]: ...
    @abstractmethod
    def get(self, model_id: int) -> Optional[ModelEntity]: ...
    @abstractmethod
    def save(self, model: ModelEntity) -> ModelEntity: ...
    @abstractmethod
    def set_active(self, model_id: int) -> Optional[ModelEntity]: ...
    @abstractmethod
    def delete(self, model_id: int) -> bool: ...


class SessionRepository(ABC):
    @abstractmethod
    def add(self, session: SessionEntity) -> SessionEntity: ...
    @abstractmethod
    def get_by_refresh(self, refresh_jti: str) -> Optional[SessionEntity]: ...
    @abstractmethod
    def list_for_user(self, user_id: str) -> List[SessionEntity]: ...
    @abstractmethod
    def revoke(self, refresh_jti: str) -> bool: ...
    @abstractmethod
    def revoke_all(self, user_id: str) -> int: ...
    @abstractmethod
    def touch(self, refresh_jti: str) -> None: ...


class BackupRepository(ABC):
    @abstractmethod
    def add(self, backup: BackupEntity) -> BackupEntity: ...
    @abstractmethod
    def list(self) -> List[BackupEntity]: ...
    @abstractmethod
    def get(self, backup_id: int) -> Optional[BackupEntity]: ...


class JobRepository(ABC):
    @abstractmethod
    def list(self) -> List[JobEntity]: ...
    @abstractmethod
    def get(self, name: str) -> Optional[JobEntity]: ...
    @abstractmethod
    def save(self, job: JobEntity) -> JobEntity: ...
