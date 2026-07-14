"""
FrameBuffer — bounded circular queue thread-safe cho frame từng camera.

Chiến lược khi đầy: drop oldest frame (giữ latest realtime).
Hỗ trợ truy vấn theo timestamp cho Evidence Engine.
"""

import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, List, Optional

from loguru import logger

from app.modules.camera.models.frame import FramePacket


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


class FrameBuffer:
    """
    Buffer frame dùng deque + Lock — thread-safe.

    Attributes:
        max_size: Số frame tối đa trong queue.
        retention_seconds: Thời gian giữ frame (circular theo thời gian).
        dropped_count: Số frame đã bị loại do queue đầy.
    """

    def __init__(
        self, max_size: int = 30, retention_seconds: Optional[float] = None
    ) -> None:
        self._max_size = max_size
        self._retention_seconds = retention_seconds
        self._deque: Deque[FramePacket] = deque(maxlen=max_size)
        self._latest: Optional[FramePacket] = None
        self._lock = threading.RLock()
        self.dropped_count: int = 0

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._deque)

    def push(self, frame: FramePacket) -> None:
        with self._lock:
            if len(self._deque) >= self._max_size and self._max_size > 0:
                self.dropped_count += 1
                logger.debug(
                    "Queue full camera_id={} — drop oldest frame",
                    frame.camera_id,
                )
            self._deque.append(frame)
            self._latest = frame
            if self._retention_seconds:
                self._evict(frame.timestamp)

    def _evict(self, now: datetime) -> None:
        if not self._retention_seconds:
            return
        cutoff = _naive(now) - timedelta(seconds=self._retention_seconds)
        while self._deque and _naive(self._deque[0].timestamp) < cutoff:
            self._deque.popleft()

    def pop(self) -> Optional[FramePacket]:
        with self._lock:
            if not self._deque:
                return None
            return self._deque.popleft()

    def latest(self) -> Optional[FramePacket]:
        with self._lock:
            return self._latest

    def get_frame(self, timestamp: datetime) -> Optional[FramePacket]:
        """Frame gần nhất với timestamp."""
        return self._nearest(timestamp)

    def get_snapshot(self, timestamp: datetime) -> Optional[FramePacket]:
        return self.get_frame(timestamp)

    def get_video(self, start: datetime, end: datetime) -> List[FramePacket]:
        s, e = _naive(start), _naive(end)
        with self._lock:
            return [
                p for p in self._deque if s <= _naive(p.timestamp) <= e
            ]

    def _nearest(self, timestamp: datetime) -> Optional[FramePacket]:
        target = _naive(timestamp)
        with self._lock:
            if not self._deque:
                return None
            best: Optional[FramePacket] = None
            best_delta = float("inf")
            for p in self._deque:
                delta = abs((_naive(p.timestamp) - target).total_seconds())
                if delta < best_delta:
                    best_delta = delta
                    best = p
            return best

    def clear(self) -> None:
        with self._lock:
            self._deque.clear()
            self._latest = None

    def drop_old_frames(self, keep: int = 1) -> int:
        with self._lock:
            removed = 0
            while len(self._deque) > keep:
                self._deque.popleft()
                removed += 1
            return removed
