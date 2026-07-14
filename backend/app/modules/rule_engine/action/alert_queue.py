"""
AlertQueue — hàng đợi in-memory chứa BehaviorEvent chờ Sprint 7 tiêu thụ.

Rule Engine KHÔNG gửi Telegram/DB — chỉ đẩy event vào queue này.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, List

from app.modules.rule_engine.event.event import BehaviorEventDTO


class AlertQueue:
    """Hàng đợi bounded, thread-safe cho alert."""

    def __init__(self, max_size: int = 1000) -> None:
        self._queue: Deque[BehaviorEventDTO] = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._total_pushed = 0

    def push(self, event: BehaviorEventDTO) -> None:
        """Đẩy event vào queue (drop-oldest khi đầy)."""
        with self._lock:
            self._queue.append(event)
            self._total_pushed += 1

    def pop_all(self) -> List[BehaviorEventDTO]:
        """Lấy và xóa toàn bộ event đang chờ (Sprint 7 sẽ dùng)."""
        with self._lock:
            items = list(self._queue)
            self._queue.clear()
            return items

    def peek_all(self) -> List[BehaviorEventDTO]:
        """Xem toàn bộ event đang chờ (không xóa)."""
        with self._lock:
            return list(self._queue)

    @property
    def size(self) -> int:
        """Số event đang chờ."""
        return len(self._queue)

    @property
    def total_pushed(self) -> int:
        """Tổng số event đã đẩy."""
        return self._total_pushed

    def clear(self) -> None:
        with self._lock:
            self._queue.clear()
