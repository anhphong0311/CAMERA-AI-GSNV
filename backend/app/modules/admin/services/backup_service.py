"""
Backup Service (Sprint 9).

Sao lưu Database / Configuration / Rule / ROI / AI Config ra file (JSON hoặc dump).
Dữ liệu cần backup được cung cấp qua "provider" callable (tôn trọng ranh giới module:
giao tiếp qua service, không đọc trực tiếp DB module khác).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from app.exceptions.base import ValidationError
from app.modules.admin.repositories.base import BackupRepository
from app.modules.admin.repositories.entities import BackupEntity
from app.modules.admin.services.audit_service import AuditService

BACKUP_KINDS = ["database", "config", "rule", "roi", "ai_config"]

# Provider trả về dict dữ liệu cho từng kind (trừ database dùng pg_dump).
DataProvider = Callable[[], Dict[str, Any]]


class BackupService:
    def __init__(
        self,
        repo: BackupRepository,
        audit: AuditService,
        base_dir: str = "./data/backups",
        providers: Optional[Dict[str, DataProvider]] = None,
        database_url: Optional[str] = None,
    ) -> None:
        self._repo = repo
        self._audit = audit
        self._base = Path(base_dir)
        self._providers = providers or {}
        self._database_url = database_url

    def register_provider(self, kind: str, provider: DataProvider) -> None:
        self._providers[kind] = provider

    def _ensure_dir(self) -> Path:
        self._base.mkdir(parents=True, exist_ok=True)
        return self._base

    def create_backup(self, kind: str, *, actor: Optional[str] = None) -> BackupEntity:
        if kind not in BACKUP_KINDS:
            raise ValidationError(f"Loại backup '{kind}' không hợp lệ.")
        self._ensure_dir()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if kind == "database":
            path, size, status = self._backup_database(ts)
        else:
            provider = self._providers.get(kind)
            data = provider() if provider else {}
            path = self._base / f"{kind}_{ts}.json"
            payload = {"kind": kind, "created_at": ts, "data": data}
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
            size = path.stat().st_size
            status = "completed"

        record = self._repo.add(
            BackupEntity(kind=kind, path=str(path), size_bytes=size, status=status, created_by=actor)
        )
        self._audit.log("backup", "backup", username=actor, target=kind, detail={"path": str(path)})
        return record

    def _backup_database(self, ts: str) -> tuple[str, int, str]:
        """Dùng pg_dump nếu có; nếu không, ghi file marker (môi trường không có DB)."""
        out = self._base / f"database_{ts}.sql"
        pg_dump = shutil.which("pg_dump")
        if pg_dump and self._database_url:
            try:
                url = self._database_url.replace("+asyncpg", "")
                with open(out, "wb") as fh:
                    subprocess.run(
                        [pg_dump, "--dbname", url, "--no-owner"],
                        stdout=fh, stderr=subprocess.PIPE, check=True, timeout=600,
                    )
                return str(out), out.stat().st_size, "completed"
            except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
                logger.warning("pg_dump thất bại: {}", exc)
        marker = self._base / f"database_{ts}.json"
        marker.write_text(
            json.dumps({"kind": "database", "note": "pg_dump unavailable", "created_at": ts}),
            "utf-8",
        )
        return str(marker), marker.stat().st_size, "skipped"

    def list(self) -> List[BackupEntity]:
        return self._repo.list()

    def get(self, backup_id: int) -> Optional[BackupEntity]:
        return self._repo.get(backup_id)
