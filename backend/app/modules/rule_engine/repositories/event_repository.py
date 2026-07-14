"""
EventRepository — kho BehaviorEvent in-memory (live + history).

KHÔNG dùng Database. Live = event chưa kết thúc; history = bounded deque.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Dict, List, Optional

from app.modules.rule_engine.event.event import BehaviorEventDTO
from app.modules.rule_engine.state.event_state import EventState


class EventRepository:
    """Lưu trữ event trong bộ nhớ."""

    def __init__(self, history_size: int = 2000) -> None:
        self._live: Dict[str, BehaviorEventDTO] = {}
        self._history: Deque[BehaviorEventDTO] = deque(maxlen=history_size)
        self._by_id: Dict[str, BehaviorEventDTO] = {}
        self._lock = threading.RLock()
        self._total = 0

    def add(self, event: BehaviorEventDTO) -> None:
        """Thêm event mới (confirmed)."""
        with self._lock:
            self._live[event.event_id] = event
            self._by_id[event.event_id] = event
            self._history.append(event)
            self._total += 1

    def end(self, event: BehaviorEventDTO) -> None:
        """Đánh dấu event kết thúc → rời khỏi live."""
        with self._lock:
            self._live.pop(event.event_id, None)

    def get(self, event_id: str) -> Optional[BehaviorEventDTO]:
        """Lấy event theo id."""
        with self._lock:
            return self._by_id.get(event_id)

    def live(self) -> List[BehaviorEventDTO]:
        """Event đang hoạt động."""
        with self._lock:
            return list(self._live.values())

    def history(
        self,
        camera_id: Optional[int] = None,
        track_id: Optional[int] = None,
        rule_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[BehaviorEventDTO]:
        """Lịch sử event (lọc tùy chọn)."""
        with self._lock:
            items = list(self._history)
        if camera_id is not None:
            items = [e for e in items if e.camera_id == camera_id]
        if track_id is not None:
            items = [e for e in items if e.track_id == track_id]
        if rule_id is not None:
            items = [e for e in items if e.rule_id == rule_id]
        return items[-limit:]

    def statistics(self) -> dict:
        """Thống kê event."""
        with self._lock:
            by_rule: Dict[str, int] = {}
            by_severity: Dict[str, int] = {}
            for e in self._history:
                by_rule[e.rule_id] = by_rule.get(e.rule_id, 0) + 1
                by_severity[e.severity.value] = (
                    by_severity.get(e.severity.value, 0) + 1
                )
            return {
                "total_events": self._total,
                "live_events": len(self._live),
                "history_size": len(self._history),
                "by_rule": by_rule,
                "by_severity": by_severity,
            }

    def clear(self) -> None:
        with self._lock:
            self._live.clear()
            self._history.clear()
            self._by_id.clear()
            self._total = 0
