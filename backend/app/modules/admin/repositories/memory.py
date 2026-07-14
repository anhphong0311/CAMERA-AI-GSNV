"""
InMemory repositories (thread-safe) cho module admin.

Là implementation mặc định khi chạy không có DB và dùng cho unit/integration test.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

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


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._data: Dict[str, UserEntity] = {}
        self._lock = threading.RLock()

    def list(self) -> List[UserEntity]:
        with self._lock:
            return list(self._data.values())

    def get(self, user_id: str) -> Optional[UserEntity]:
        with self._lock:
            return self._data.get(user_id)

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        with self._lock:
            for u in self._data.values():
                if u.username == username:
                    return u
            return None

    def save(self, user: UserEntity) -> UserEntity:
        with self._lock:
            self._data[user.id] = user
            return user

    def delete(self, user_id: str) -> bool:
        with self._lock:
            return self._data.pop(user_id, None) is not None


class InMemoryRoleRepository(RoleRepository):
    def __init__(self) -> None:
        self._data: Dict[str, RoleEntity] = {}
        self._lock = threading.RLock()

    def list(self) -> List[RoleEntity]:
        with self._lock:
            return list(self._data.values())

    def get(self, name: str) -> Optional[RoleEntity]:
        with self._lock:
            return self._data.get(name)

    def save(self, role: RoleEntity) -> RoleEntity:
        with self._lock:
            self._data[role.name] = role
            return role

    def delete(self, name: str) -> bool:
        with self._lock:
            return self._data.pop(name, None) is not None


class InMemoryAuditRepository(AuditRepository):
    def __init__(self, capacity: int = 10000) -> None:
        self._data: List[AuditEntity] = []
        self._seq = 0
        self._capacity = capacity
        self._lock = threading.RLock()

    def add(self, entry: AuditEntity) -> AuditEntity:
        with self._lock:
            self._seq += 1
            entry.id = self._seq
            self._data.append(entry)
            if len(self._data) > self._capacity:
                self._data = self._data[-self._capacity :]
            return entry

    def query(
        self,
        *,
        action: Optional[str] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntity]:
        with self._lock:
            rows = list(reversed(self._data))
        if action:
            rows = [r for r in rows if r.action == action]
        if module:
            rows = [r for r in rows if r.module == module]
        if user_id:
            rows = [r for r in rows if r.user_id == user_id]
        return rows[:limit]


class InMemoryConfigRepository(ConfigRepository):
    def __init__(self) -> None:
        self._data: Dict[str, ConfigEntity] = {}
        self._lock = threading.RLock()

    def all(self) -> List[ConfigEntity]:
        with self._lock:
            return list(self._data.values())

    def get(self, key: str) -> Optional[ConfigEntity]:
        with self._lock:
            return self._data.get(key)

    def section(self, section: str) -> List[ConfigEntity]:
        with self._lock:
            return [c for c in self._data.values() if c.section == section]

    def set(self, entry: ConfigEntity) -> ConfigEntity:
        with self._lock:
            entry.updated_at = datetime.now(timezone.utc)
            self._data[entry.key] = entry
            return entry

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._data.pop(key, None) is not None


class InMemoryModelRepository(ModelRepository):
    def __init__(self) -> None:
        self._data: Dict[int, ModelEntity] = {}
        self._seq = 0
        self._lock = threading.RLock()

    def list(self) -> List[ModelEntity]:
        with self._lock:
            return list(self._data.values())

    def get(self, model_id: int) -> Optional[ModelEntity]:
        with self._lock:
            return self._data.get(model_id)

    def save(self, model: ModelEntity) -> ModelEntity:
        with self._lock:
            if model.id is None:
                self._seq += 1
                model.id = self._seq
            self._data[model.id] = model
            return model

    def set_active(self, model_id: int) -> Optional[ModelEntity]:
        with self._lock:
            target = self._data.get(model_id)
            if target is None:
                return None
            for m in self._data.values():
                if m.name == target.name:
                    m.is_active = m.id == model_id
                    m.status = "active" if m.id == model_id else "inactive"
            return target

    def delete(self, model_id: int) -> bool:
        with self._lock:
            return self._data.pop(model_id, None) is not None


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._data: Dict[str, SessionEntity] = {}  # keyed by refresh_jti
        self._lock = threading.RLock()

    def add(self, session: SessionEntity) -> SessionEntity:
        with self._lock:
            self._data[session.refresh_jti] = session
            return session

    def get_by_refresh(self, refresh_jti: str) -> Optional[SessionEntity]:
        with self._lock:
            return self._data.get(refresh_jti)

    def list_for_user(self, user_id: str) -> List[SessionEntity]:
        with self._lock:
            return [s for s in self._data.values() if s.user_id == user_id]

    def revoke(self, refresh_jti: str) -> bool:
        with self._lock:
            s = self._data.get(refresh_jti)
            if s is None:
                return False
            s.revoked = True
            return True

    def revoke_all(self, user_id: str) -> int:
        with self._lock:
            count = 0
            for s in self._data.values():
                if s.user_id == user_id and not s.revoked:
                    s.revoked = True
                    count += 1
            return count

    def touch(self, refresh_jti: str) -> None:
        with self._lock:
            s = self._data.get(refresh_jti)
            if s is not None:
                s.last_activity = datetime.now(timezone.utc)


class InMemoryBackupRepository(BackupRepository):
    def __init__(self) -> None:
        self._data: Dict[int, BackupEntity] = {}
        self._seq = 0
        self._lock = threading.RLock()

    def add(self, backup: BackupEntity) -> BackupEntity:
        with self._lock:
            self._seq += 1
            backup.id = self._seq
            self._data[backup.id] = backup
            return backup

    def list(self) -> List[BackupEntity]:
        with self._lock:
            return sorted(self._data.values(), key=lambda b: b.id or 0, reverse=True)

    def get(self, backup_id: int) -> Optional[BackupEntity]:
        with self._lock:
            return self._data.get(backup_id)


class InMemoryJobRepository(JobRepository):
    def __init__(self) -> None:
        self._data: Dict[str, JobEntity] = {}
        self._lock = threading.RLock()

    def list(self) -> List[JobEntity]:
        with self._lock:
            return list(self._data.values())

    def get(self, name: str) -> Optional[JobEntity]:
        with self._lock:
            return self._data.get(name)

    def save(self, job: JobEntity) -> JobEntity:
        with self._lock:
            self._data[job.name] = job
            return job
