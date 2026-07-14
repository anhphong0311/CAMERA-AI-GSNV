"""Audit Service (Sprint 9) — ghi & truy vấn nhật ký kiểm toán."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from app.modules.admin.repositories.base import AuditRepository
from app.modules.admin.repositories.entities import AuditEntity


class AuditService:
    """Ghi nhận mọi hành động (login/logout/CRUD/rule/camera/config/model...)."""

    def __init__(self, repo: AuditRepository) -> None:
        self._repo = repo

    def log(
        self,
        action: str,
        module: str,
        *,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        target: Optional[str] = None,
        status: str = "success",
        ip: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> AuditEntity:
        entry = AuditEntity(
            action=action,
            module=module,
            user_id=user_id,
            username=username,
            target=target,
            status=status,
            ip=ip,
            detail=detail,
        )
        saved = self._repo.add(entry)
        logger.bind(audit=True).info(
            "AUDIT {module}/{action} user={user} target={target} status={status}",
            module=module,
            action=action,
            user=username or user_id or "-",
            target=target or "-",
            status=status,
        )
        return saved

    def query(
        self,
        *,
        action: Optional[str] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntity]:
        return self._repo.query(
            action=action, module=module, user_id=user_id, limit=limit
        )
