"""
Priority Queue (Sprint 10) — thread-safe, drop-oldest/newest.

Dùng cho inference/task queue với mức ưu tiên (camera quan trọng trước).
"""

from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass(order=True)
class _PriorityItem(Generic[T]):
    priority: int
    seq: int
    enqueued_at: float = field(compare=False)
    payload: Any = field(compare=False)


class PriorityQueue(Generic[T]):
    """Min-heap priority queue (priority nhỏ = cao hơn). Thread-safe."""

    def __init__(self, max_size: int = 32, drop_policy: str = "oldest") -> None:
        self._max_size = max_size
        self._drop_policy = drop_policy
        self._heap: List[_PriorityItem[T]] = []
        self._seq = 0
        self._lock = threading.Lock()
        self.dropped = 0

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def put(self, item: T, priority: int = 5) -> None:
        with self._lock:
            if len(self._heap) >= self._max_size:
                self.dropped += 1
                if self._drop_policy == "oldest" and self._heap:
                    heapq.heappop(self._heap)
                elif self._drop_policy == "newest":
                    return
            self._seq += 1
            heapq.heappush(
                self._heap,
                _PriorityItem(priority, self._seq, time.monotonic(), item),
            )

    def get(self) -> Optional[T]:
        with self._lock:
            if not self._heap:
                return None
            return heapq.heappop(self._heap).payload

    def clear(self) -> None:
        with self._lock:
            self._heap.clear()

    def stats(self) -> dict:
        with self._lock:
            ages = [time.monotonic() - x.enqueued_at for x in self._heap] if self._heap else []
        return {
            "size": len(self._heap),
            "max_size": self._max_size,
            "dropped": self.dropped,
            "max_age_s": round(max(ages), 3) if ages else 0.0,
            "avg_age_s": round(sum(ages) / len(ages), 3) if ages else 0.0,
        }
