"""
EventStore — kho lưu EventRecord.

Interface đồng bộ (sync) + bản in-memory mặc định (dùng runtime & test).
SqlEventStore (async) ở module riêng cho persistence Database.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Dict, List, Optional

from app.modules.event.schemas.records import EventRecord
from app.modules.event.schemas.status import EventStatus


class EventStore(ABC):
    """Kho EventRecord (sync)."""

    @abstractmethod
    def save(self, record: EventRecord) -> EventRecord:
        """Lưu/ghi đè record."""

    @abstractmethod
    def get(self, event_id: str) -> Optional[EventRecord]:
        """Lấy record theo id."""

    @abstractmethod
    def list(
        self,
        camera_id: Optional[int] = None,
        rule_id: Optional[str] = None,
        status: Optional[EventStatus] = None,
        limit: int = 200,
    ) -> List[EventRecord]:
        """Liệt kê record (lọc)."""

    @abstractmethod
    def live(self) -> List[EventRecord]:
        """Record đang xử lý (chưa COMPLETED/FAILED)."""

    @abstractmethod
    def statistics(self) -> dict:
        """Thống kê."""


class InMemoryEventStore(EventStore):
    """Lưu EventRecord trong bộ nhớ (bounded history)."""

    _TERMINAL = {EventStatus.COMPLETED, EventStatus.FAILED}

    def __init__(self, history_size: int = 2000) -> None:
        self._by_id: Dict[str, EventRecord] = {}
        self._order: Deque[str] = deque(maxlen=history_size)
        self._lock = threading.RLock()
        self._total = 0

    def save(self, record: EventRecord) -> EventRecord:
        with self._lock:
            if record.event_id not in self._by_id:
                self._total += 1
                # deque maxlen tự loại id cũ nhất; _prune đồng bộ lại map
                self._order.append(record.event_id)
                self._prune()
            self._by_id[record.event_id] = record
            return record

    def _prune(self) -> None:
        """Đồng bộ map với order (loại id không còn trong order)."""
        valid = set(self._order)
        if len(self._by_id) > len(valid):
            for k in list(self._by_id.keys()):
                if k not in valid:
                    del self._by_id[k]

    def get(self, event_id: str) -> Optional[EventRecord]:
        with self._lock:
            return self._by_id.get(event_id)

    def list(
        self,
        camera_id: Optional[int] = None,
        rule_id: Optional[str] = None,
        status: Optional[EventStatus] = None,
        limit: int = 200,
    ) -> List[EventRecord]:
        with self._lock:
            items = [self._by_id[i] for i in self._order if i in self._by_id]
        if camera_id is not None:
            items = [e for e in items if e.camera_id == camera_id]
        if rule_id is not None:
            items = [e for e in items if e.rule_id == rule_id]
        if status is not None:
            items = [e for e in items if e.status == status]
        return items[-limit:]

    def live(self) -> List[EventRecord]:
        with self._lock:
            return [
                self._by_id[i]
                for i in self._order
                if i in self._by_id and self._by_id[i].status not in self._TERMINAL
            ]

    def statistics(self) -> dict:
        with self._lock:
            by_status: Dict[str, int] = {}
            by_rule: Dict[str, int] = {}
            notifications = 0
            for i in self._order:
                e = self._by_id.get(i)
                if not e:
                    continue
                by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
                by_rule[e.rule_id] = by_rule.get(e.rule_id, 0) + 1
                notifications += len(e.notifications)
            return {
                "total_events": self._total,
                "stored": len(self._by_id),
                "by_status": by_status,
                "by_rule": by_rule,
                "notifications": notifications,
            }

    def clear(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._order.clear()
            self._total = 0
