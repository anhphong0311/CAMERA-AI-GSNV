"""
Queue — hàng đợi in-memory thread-safe cho Event và Notification.

Notification Queue tách biệt: Behavior Event → Notification Queue → Worker → Telegram.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BoundedQueue(Generic[T]):
    """Hàng đợi FIFO bounded, thread-safe."""

    def __init__(self, max_size: int = 1000) -> None:
        self._items: Deque[T] = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._total_enqueued = 0
        self._total_dequeued = 0

    def put(self, item: T) -> None:
        """Thêm item (drop-oldest khi đầy)."""
        with self._lock:
            self._items.append(item)
            self._total_enqueued += 1

    def get(self) -> Optional[T]:
        """Lấy item đầu (None nếu rỗng)."""
        with self._lock:
            if not self._items:
                return None
            self._total_dequeued += 1
            return self._items.popleft()

    def drain(self) -> List[T]:
        """Lấy toàn bộ item hiện có."""
        with self._lock:
            items = list(self._items)
            self._total_dequeued += len(items)
            self._items.clear()
            return items

    @property
    def size(self) -> int:
        return len(self._items)

    @property
    def total_enqueued(self) -> int:
        return self._total_enqueued

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
