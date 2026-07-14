"""
Scheduler Service (Sprint 9) — điều phối job định kỳ và trạng thái.

Đăng ký: daily cleanup, backup, report generation, storage/video/snapshot cleanup.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from app.modules.admin.scheduler.scheduler import AsyncScheduler
from app.modules.admin.services.audit_service import AuditService
from app.modules.admin.services.backup_service import BackupService
from app.modules.admin.services.config_service import ConfigService
from app.modules.admin.services.storage_service import StorageService


class SchedulerService:
    def __init__(
        self,
        scheduler: AsyncScheduler,
        storage: StorageService,
        backup: BackupService,
        config: ConfigService,
        audit: AuditService,
    ) -> None:
        self._scheduler = scheduler
        self._storage = storage
        self._backup = backup
        self._config = config
        self._audit = audit

    def register_default_jobs(self) -> None:
        """Đăng ký các job mặc định (interval lấy từ config)."""
        day = 86400
        self._scheduler.register("daily_cleanup", self._job_daily_cleanup, day)
        self._scheduler.register("storage_cleanup", self._job_storage_cleanup, day)
        self._scheduler.register("video_cleanup", self._job_video_cleanup, day)
        self._scheduler.register("snapshot_cleanup", self._job_snapshot_cleanup, day)
        self._scheduler.register("report_generation", self._job_report, day)
        interval = int(self._config.get_value("backup.interval_seconds", day) or day)
        enabled = bool(self._config.get_value("backup.auto_enabled", True))
        self._scheduler.register("auto_backup", self._job_backup, interval, enabled)

    # ----- Jobs -----
    def _job_daily_cleanup(self) -> None:
        self._storage.cleanup_all(actor="scheduler")

    def _job_storage_cleanup(self) -> None:
        self._storage.cleanup_all(actor="scheduler")

    def _job_video_cleanup(self) -> None:
        self._storage.cleanup("video", actor="scheduler")

    def _job_snapshot_cleanup(self) -> None:
        self._storage.cleanup("snapshot", actor="scheduler")

    def _job_report(self) -> None:
        logger.info("Scheduler: report_generation tick")
        self._audit.log("report", "scheduler", username="scheduler", target="daily_report")

    def _job_backup(self) -> None:
        self._backup.create_backup("config", actor="scheduler")

    # ----- Control API -----
    def status(self) -> List[Dict[str, Any]]:
        return self._scheduler.status()

    async def run_now(self, name: str) -> None:
        await self._scheduler.run_now(name)

    def set_enabled(self, name: str, enabled: bool, *, actor: Optional[str] = None) -> bool:
        ok = self._scheduler.set_enabled(name, enabled)
        if ok:
            self._audit.log(
                "toggle", "scheduler", username=actor, target=name,
                detail={"enabled": enabled},
            )
        return ok
