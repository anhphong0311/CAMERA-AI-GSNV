"""
Restore Service (Sprint 9).

Khôi phục Config / Rule / ROI (và Database ở mức hướng dẫn). Handler khôi phục cho
từng kind được inject qua callable → module đích tự áp dụng qua service của nó.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.exceptions.base import NotFoundError, ValidationError
from app.modules.admin.repositories.base import BackupRepository
from app.modules.admin.services.audit_service import AuditService

RestoreHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


class RestoreService:
    def __init__(
        self,
        repo: BackupRepository,
        audit: AuditService,
        handlers: Optional[Dict[str, RestoreHandler]] = None,
    ) -> None:
        self._repo = repo
        self._audit = audit
        self._handlers = handlers or {}

    def register_handler(self, kind: str, handler: RestoreHandler) -> None:
        self._handlers[kind] = handler

    def restore(self, backup_id: int, *, actor: Optional[str] = None) -> Dict[str, Any]:
        record = self._repo.get(backup_id)
        if record is None:
            raise NotFoundError("Backup", backup_id)
        path = Path(record.path)
        if not path.exists():
            raise NotFoundError("Backup file", record.path)
        if record.kind == "database":
            raise ValidationError(
                "Khôi phục Database phải chạy thủ công bằng psql/pg_restore theo Restore Guide."
            )

        payload = json.loads(path.read_text("utf-8"))
        data = payload.get("data", {})
        handler = self._handlers.get(record.kind)
        summary: Dict[str, Any] = {"kind": record.kind, "applied": False}
        if handler is not None:
            summary = {**summary, **handler(data), "applied": True}
        else:
            summary["items"] = len(data) if hasattr(data, "__len__") else 0
        self._audit.log(
            "restore", "restore", username=actor, target=record.kind,
            detail={"backup_id": backup_id},
        )
        return summary
