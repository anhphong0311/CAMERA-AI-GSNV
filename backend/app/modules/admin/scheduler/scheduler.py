"""
Async Scheduler (Sprint 9) — cron-lite dựa trên asyncio (không thêm dependency nặng).

Chạy các job định kỳ: daily cleanup, backup, report generation, storage/video/snapshot
cleanup. Trạng thái job (enabled/interval/last_run) được lưu qua JobRepository (DB).
"""

from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List, Optional, Union

from loguru import logger

from app.modules.admin.repositories.base import JobRepository
from app.modules.admin.repositories.entities import JobEntity

JobFunc = Callable[[], Union[None, Awaitable[None]]]


@dataclass
class _Job:
    name: str
    func: JobFunc
    interval_seconds: int
    enabled: bool = True
    next_run: float = field(default_factory=time.monotonic)
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None


class AsyncScheduler:
    """Bộ lập lịch chạy nền trong event loop."""

    def __init__(self, repo: JobRepository, tick_seconds: float = 1.0) -> None:
        self._repo = repo
        self._jobs: Dict[str, _Job] = {}
        self._tick = tick_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def register(
        self, name: str, func: JobFunc, interval_seconds: int, enabled: bool = True
    ) -> None:
        existing = self._repo.get(name)
        if existing is not None:
            interval_seconds = existing.interval_seconds
            enabled = existing.enabled
        else:
            self._repo.save(
                JobEntity(name=name, interval_seconds=interval_seconds, enabled=enabled)
            )
        self._jobs[name] = _Job(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            enabled=enabled,
            next_run=time.monotonic() + interval_seconds,
        )

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Scheduler started with {} jobs", len(self._jobs))

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            now = time.monotonic()
            for job in list(self._jobs.values()):
                if job.enabled and now >= job.next_run:
                    await self._run(job)
                    job.next_run = time.monotonic() + job.interval_seconds
            await asyncio.sleep(self._tick)

    async def _run(self, job: _Job) -> None:
        try:
            result = job.func()
            if inspect.isawaitable(result):
                await result
            job.last_status = "success"
        except Exception as exc:  # noqa: BLE001
            job.last_status = "failed"
            logger.error("Job '{}' lỗi: {}", job.name, exc)
        job.last_run = datetime.now(timezone.utc)
        record = self._repo.get(job.name) or JobEntity(
            name=job.name, interval_seconds=job.interval_seconds, enabled=job.enabled
        )
        record.last_run = job.last_run
        record.last_status = job.last_status
        record.interval_seconds = job.interval_seconds
        record.enabled = job.enabled
        self._repo.save(record)

    async def run_now(self, name: str) -> None:
        job = self._jobs.get(name)
        if job is not None:
            await self._run(job)

    def set_enabled(self, name: str, enabled: bool) -> bool:
        job = self._jobs.get(name)
        if job is None:
            return False
        job.enabled = enabled
        record = self._repo.get(name)
        if record is not None:
            record.enabled = enabled
            self._repo.save(record)
        return True

    def status(self) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for job in self._jobs.values():
            out.append(
                {
                    "name": job.name,
                    "interval_seconds": job.interval_seconds,
                    "enabled": job.enabled,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "last_status": job.last_status,
                }
            )
        return out
