"""
Memory & Frame pools (Sprint 10) — tái sử dụng buffer, giảm allocation/GC.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Optional, Tuple

import numpy as np


class FramePool:
    """Pool ndarray BGR cố định kích thước — get/return thread-safe."""

    def __init__(self, pool_size: int = 64, default_shape: Tuple[int, int, int] = (640, 640, 3)) -> None:
        self._pool_size = pool_size
        self._shape = default_shape
        self._free: Deque[np.ndarray] = deque(maxlen=pool_size)
        self._lock = threading.Lock()
        self._allocated = 0
        self._hits = 0
        self._misses = 0

    def acquire(self, shape: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        shape = shape or self._shape
        with self._lock:
            if self._free:
                self._hits += 1
                buf = self._free.popleft()
                if buf.shape == shape:
                    return buf
            self._misses += 1
            self._allocated += 1
            return np.zeros(shape, dtype=np.uint8)

    def release(self, frame: np.ndarray) -> None:
        with self._lock:
            if len(self._free) < self._pool_size:
                self._free.append(frame)

    def stats(self) -> dict:
        with self._lock:
            return {
                "pool_size": self._pool_size,
                "free": len(self._free),
                "allocated_total": self._allocated,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / max(self._hits + self._misses, 1) * 100, 1),
            }


class BufferPool:
    """Pool buffer bytes/bytearray cho encode/network."""

    def __init__(self, pool_size: int = 32, buffer_size: int = 65536) -> None:
        self._pool_size = pool_size
        self._buffer_size = buffer_size
        self._free: Deque[bytearray] = deque(maxlen=pool_size)
        self._lock = threading.Lock()

    def acquire(self) -> bytearray:
        with self._lock:
            if self._free:
                return self._free.popleft()
            return bytearray(self._buffer_size)

    def release(self, buf: bytearray) -> None:
        with self._lock:
            if len(self._free) < self._pool_size:
                self._free.append(buf)

    def stats(self) -> dict:
        with self._lock:
            return {"pool_size": self._pool_size, "free": len(self._free)}
