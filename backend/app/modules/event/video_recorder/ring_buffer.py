"""
RingBuffer — giữ N giây frame gần nhất của mỗi camera trong RAM.

Khi event xảy ra, cắt cửa sổ [t-pre, t+post] để xuất video evidence.
KHÔNG lưu toàn bộ video — chỉ giữ buffer tạm thời.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional

import numpy as np


def _naive(dt: datetime) -> datetime:
    """Bỏ tzinfo để so sánh an toàn giữa aware/naive."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


@dataclass
class BufferedFrame:
    """Một frame kèm timestamp."""

    timestamp: datetime
    frame: np.ndarray


class CameraRingBuffer:
    """Ring buffer frame cho một camera (giới hạn theo thời gian)."""

    def __init__(self, seconds: float, fps: int) -> None:
        self._seconds = seconds
        maxlen = max(1, int(seconds * fps) + fps)
        self._frames: Deque[BufferedFrame] = deque(maxlen=maxlen)
        self._lock = threading.RLock()

    def push(self, frame: np.ndarray, timestamp: Optional[datetime] = None) -> None:
        """Thêm frame mới."""
        ts = _naive(timestamp) if timestamp else datetime.now()
        with self._lock:
            self._frames.append(BufferedFrame(ts, frame))
            self._evict(ts)

    def _evict(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self._seconds)
        while self._frames and self._frames[0].timestamp < cutoff:
            self._frames.popleft()

    def latest(self) -> Optional[np.ndarray]:
        """Frame mới nhất (dùng cho snapshot)."""
        with self._lock:
            return self._frames[-1].frame if self._frames else None

    def window(
        self, center: datetime, pre_seconds: float, post_seconds: float
    ) -> List[np.ndarray]:
        """Các frame trong [center-pre, center+post]."""
        c = _naive(center)
        start = c - timedelta(seconds=pre_seconds)
        end = c + timedelta(seconds=post_seconds)
        with self._lock:
            return [
                bf.frame for bf in self._frames if start <= bf.timestamp <= end
            ]

    @property
    def size(self) -> int:
        """Số frame đang giữ."""
        return len(self._frames)

    def clear(self) -> None:
        with self._lock:
            self._frames.clear()


class RingBufferManager:
    """Quản lý ring buffer theo camera."""

    def __init__(self, seconds: float, fps: int) -> None:
        self._seconds = seconds
        self._fps = fps
        self._buffers: Dict[int, CameraRingBuffer] = {}
        self._lock = threading.RLock()

    def buffer(self, camera_id: int) -> CameraRingBuffer:
        """Lấy/tạo ring buffer cho camera."""
        with self._lock:
            buf = self._buffers.get(camera_id)
            if buf is None:
                buf = CameraRingBuffer(self._seconds, self._fps)
                self._buffers[camera_id] = buf
            return buf

    def push(
        self, camera_id: int, frame: np.ndarray, timestamp: Optional[datetime] = None
    ) -> None:
        """Đẩy frame vào buffer của camera."""
        self.buffer(camera_id).push(frame, timestamp)

    def latest(self, camera_id: int) -> Optional[np.ndarray]:
        """Frame mới nhất của camera."""
        with self._lock:
            buf = self._buffers.get(camera_id)
        return buf.latest() if buf else None

    def stats(self) -> dict:
        """Thống kê buffer."""
        with self._lock:
            return {
                "cameras": len(self._buffers),
                "frames": {cid: b.size for cid, b in self._buffers.items()},
            }

    def clear(self) -> None:
        with self._lock:
            for b in self._buffers.values():
                b.clear()
            self._buffers.clear()
