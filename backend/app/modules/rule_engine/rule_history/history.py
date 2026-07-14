"""
RuleHistory — lịch sử thực thi rule (in-memory, bounded) phục vụ debug/thống kê.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Deque, List


@dataclass
class RuleExecution:
    """Bản ghi một lần chạy rule cho một track."""

    timestamp: datetime
    rule_id: str
    track_id: int
    camera_id: int
    base_active: bool
    fired: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "rule_id": self.rule_id,
            "track_id": self.track_id,
            "camera_id": self.camera_id,
            "base_active": self.base_active,
            "fired": self.fired,
        }


class RuleHistory:
    """Lưu lịch sử thực thi rule."""

    def __init__(self, max_size: int = 1000) -> None:
        self._items: Deque[RuleExecution] = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._executed = 0
        self._fired = 0

    def record(
        self,
        now: datetime,
        rule_id: str,
        track_id: int,
        camera_id: int,
        base_active: bool,
        fired: bool,
    ) -> None:
        """Ghi nhận một lần chạy rule."""
        with self._lock:
            self._items.append(
                RuleExecution(now, rule_id, track_id, camera_id, base_active, fired)
            )
            self._executed += 1
            if fired:
                self._fired += 1

    def recent(self, limit: int = 100) -> List[RuleExecution]:
        """Các bản ghi gần nhất."""
        with self._lock:
            return list(self._items)[-limit:]

    def stats(self) -> dict[str, int]:
        """Thống kê thực thi."""
        return {"executed": self._executed, "fired": self._fired}

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._executed = 0
            self._fired = 0
