"""
AI Model Management Service (Sprint 9).

QUẢN LÝ metadata phiên bản model (upload/switch/rollback/version/status/benchmark).
KHÔNG thay đổi Detection/AI Engine — chỉ theo dõi phiên bản & trạng thái.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.exceptions.base import ConflictError, NotFoundError
from app.modules.admin.repositories.base import ModelRepository
from app.modules.admin.repositories.entities import ModelEntity
from app.modules.admin.services.audit_service import AuditService


class ModelService:
    """Vòng đời phiên bản AI model."""

    def __init__(self, repo: ModelRepository, audit: AuditService) -> None:
        self._repo = repo
        self._audit = audit

    def list(self) -> List[ModelEntity]:
        return self._repo.list()

    def get(self, model_id: int) -> ModelEntity:
        model = self._repo.get(model_id)
        if model is None:
            raise NotFoundError("Model", model_id)
        return model

    def register(
        self,
        *,
        name: str,
        version: str,
        path: str,
        uploaded_by: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> ModelEntity:
        model = ModelEntity(
            name=name, version=version, path=path,
            uploaded_by=uploaded_by, metrics=metrics,
        )
        saved = self._repo.save(model)
        self._audit.log(
            "upload", "models", username=uploaded_by, target=f"{name}:{version}"
        )
        return saved

    def switch(self, model_id: int, *, actor: Optional[str] = None) -> ModelEntity:
        model = self.get(model_id)
        self._repo.set_active(model_id)
        self._audit.log(
            "switch", "models", username=actor, target=f"{model.name}:{model.version}"
        )
        return self.get(model_id)

    def rollback(self, name: str, *, actor: Optional[str] = None) -> ModelEntity:
        versions = [m for m in self._repo.list() if m.name == name]
        if not versions:
            raise NotFoundError("Model", name)
        versions.sort(key=lambda m: m.created_at, reverse=True)
        current = next((m for m in versions if m.is_active), None)
        previous = next((m for m in versions if not m.is_active), None)
        if previous is None:
            raise ConflictError("Không có phiên bản trước để rollback.")
        self._repo.set_active(previous.id)  # type: ignore[arg-type]
        self._audit.log(
            "rollback", "models", username=actor,
            target=f"{name}:{previous.version}",
            detail={"from": current.version if current else None},
        )
        return self.get(previous.id)  # type: ignore[arg-type]

    def benchmark(
        self, model_id: int, metrics: Dict[str, Any], *, actor: Optional[str] = None
    ) -> ModelEntity:
        model = self.get(model_id)
        model.metrics = {**(model.metrics or {}), **metrics}
        saved = self._repo.save(model)
        self._audit.log(
            "benchmark", "models", username=actor,
            target=f"{model.name}:{model.version}", detail=metrics,
        )
        return saved

    def delete(self, model_id: int, *, actor: Optional[str] = None) -> None:
        model = self.get(model_id)
        if model.is_active:
            raise ConflictError("Không thể xoá model đang active.")
        self._repo.delete(model_id)
        self._audit.log(
            "delete", "models", username=actor, target=f"{model.name}:{model.version}"
        )

    def status(self) -> Dict[str, Any]:
        active = {m.name: m.to_dict() for m in self._repo.list() if m.is_active}
        return {"active": active, "total": len(self._repo.list())}
