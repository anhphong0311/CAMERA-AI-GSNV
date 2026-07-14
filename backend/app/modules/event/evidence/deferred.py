"""Deferred video jobs — chờ post-roll trước khi gửi Telegram."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.modules.event.schemas.records import EventRecord


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DeferredVideoJob:
    """Job chờ đủ post-roll để xuất video."""

    record: EventRecord
    evidence_time: datetime
    ready_at: datetime
    created_at: datetime = field(default_factory=_now)


class DeferredVideoQueue:
    """Hàng đợi job video evidence (thread-safe, không block camera)."""

    def __init__(self) -> None:
        self._jobs: List[DeferredVideoJob] = []
        self._lock = threading.RLock()

    def add(self, job: DeferredVideoJob) -> None:
        with self._lock:
            self._jobs.append(job)

    def ready(self, now: Optional[datetime] = None) -> List[DeferredVideoJob]:
        ts = now or _now()
        with self._lock:
            ready = [j for j in self._jobs if j.ready_at <= ts]
            self._jobs = [j for j in self._jobs if j.ready_at > ts]
            return ready

    def pending(self) -> int:
        with self._lock:
            return len(self._jobs)

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()
