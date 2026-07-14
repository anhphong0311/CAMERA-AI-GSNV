"""
Storage Management Service (Sprint 9).

Video/Snapshot/Event/Log retention + auto cleanup + disk usage. Ngưỡng retention lấy
từ Configuration Center (DB), không hardcode.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.modules.admin.services.audit_service import AuditService
from app.modules.admin.services.config_service import ConfigService


class StorageService:
    def __init__(self, config: ConfigService, audit: AuditService) -> None:
        self._config = config
        self._audit = audit

    def retention(self) -> Dict[str, int]:
        return {
            "video_days": int(self._config.get_value("retention.video_days", 30) or 30),
            "snapshot_days": int(self._config.get_value("retention.snapshot_days", 30) or 30),
            "event_days": int(self._config.get_value("retention.event_days", 90) or 90),
            "log_days": int(self._config.get_value("retention.log_days", 30) or 30),
        }

    def _paths(self) -> Dict[str, str]:
        return {
            "video": str(self._config.get_value("storage.video_path", "./data/videos")),
            "snapshot": str(self._config.get_value("storage.snapshot_path", "./data/snapshots")),
        }

    def disk_usage(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name, p in self._paths().items():
            path = Path(p)
            target = path if path.exists() else Path(".")
            try:
                total, used, free = shutil.disk_usage(str(target))
                result[name] = {
                    "path": p,
                    "total_gb": round(total / 1e9, 2),
                    "used_gb": round(used / 1e9, 2),
                    "free_gb": round(free / 1e9, 2),
                    "percent": round(used / total * 100, 1) if total else 0.0,
                }
            except OSError:
                result[name] = {"path": p, "error": "unavailable"}
        return result

    def _cleanup_dir(self, directory: str, max_age_days: int) -> Dict[str, int]:
        path = Path(directory)
        removed = 0
        freed = 0
        if not path.exists() or max_age_days <= 0:
            return {"removed": 0, "freed_bytes": 0}
        cutoff = time.time() - max_age_days * 86400
        for f in path.rglob("*"):
            if f.is_file() and f.stat().st_mtime < cutoff:
                try:
                    size = f.stat().st_size
                    f.unlink()
                    removed += 1
                    freed += size
                except OSError as exc:  # pragma: no cover
                    logger.warning("Không xoá được {}: {}", f, exc)
        return {"removed": removed, "freed_bytes": freed}

    def cleanup(self, kind: str, *, actor: Optional[str] = None) -> Dict[str, int]:
        retention = self.retention()
        paths = self._paths()
        mapping = {
            "video": (paths["video"], retention["video_days"]),
            "snapshot": (paths["snapshot"], retention["snapshot_days"]),
        }
        if kind not in mapping:
            return {"removed": 0, "freed_bytes": 0}
        directory, days = mapping[kind]
        result = self._cleanup_dir(directory, days)
        self._audit.log("cleanup", "storage", username=actor, target=kind, detail=result)
        return result

    def cleanup_all(self, *, actor: Optional[str] = None) -> Dict[str, Any]:
        return {kind: self.cleanup(kind, actor=actor) for kind in ["video", "snapshot"]}

    def kinds(self) -> List[str]:
        return ["video", "snapshot"]
