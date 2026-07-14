"""
EvidenceFrameBuffer — circular buffer theo thời gian cho mỗi camera.

Duy trì 15~30 giây frame gần nhất. Hỗ trợ truy vấn theo timestamp
(không đọc lại RTSP).
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


@dataclass
class BufferedFrame:
    """Frame kèm timestamp và index."""

    timestamp: datetime
    frame: np.ndarray
    frame_index: int


class EvidenceFrameBuffer:
    """Circular buffer frame theo thời gian cho một camera."""

    def __init__(self, seconds: float, fps: int) -> None:
        self._seconds = seconds
        self._fps = fps
        maxlen = max(1, int(seconds * fps) + fps)
        self._frames: Deque[BufferedFrame] = deque(maxlen=maxlen)
        self._lock = threading.RLock()
        self._frame_counter = 0

    def push(
        self,
        frame: np.ndarray,
        timestamp: Optional[datetime] = None,
        frame_index: Optional[int] = None,
    ) -> int:
        """Thêm frame; trả frame_index."""
        ts = _naive(timestamp) if timestamp else datetime.now()
        with self._lock:
            if frame_index is None:
                self._frame_counter += 1
                idx = self._frame_counter
            else:
                idx = frame_index
                self._frame_counter = max(self._frame_counter, idx)
            self._frames.append(BufferedFrame(ts, frame, idx))
            self._evict(ts)
            return idx

    def _evict(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self._seconds)
        while self._frames and self._frames[0].timestamp < cutoff:
            self._frames.popleft()

    def latest(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frames[-1].frame if self._frames else None

    def latest_index(self) -> Optional[int]:
        with self._lock:
            return self._frames[-1].frame_index if self._frames else None

    def get_frame(self, timestamp: datetime) -> Optional[np.ndarray]:
        """Frame gần nhất với timestamp."""
        bf = self._nearest_buffered(timestamp)
        return bf.frame if bf else None

    def get_snapshot(self, timestamp: datetime) -> Optional[np.ndarray]:
        """Alias get_frame — snapshot tại thời điểm."""
        return self.get_frame(timestamp)

    def get_video(
        self, start: datetime, end: datetime
    ) -> List[np.ndarray]:
        """Các frame trong [start, end]."""
        s, e = _naive(start), _naive(end)
        with self._lock:
            return [bf.frame for bf in self._frames if s <= bf.timestamp <= e]

    def window(
        self, center: datetime, pre_seconds: float, post_seconds: float
    ) -> List[np.ndarray]:
        c = _naive(center)
        return self.get_video(
            c - timedelta(seconds=pre_seconds),
            c + timedelta(seconds=post_seconds),
        )

    def frame_index_at(self, timestamp: datetime) -> Optional[int]:
        bf = self._nearest_buffered(timestamp)
        return bf.frame_index if bf else None

    def _nearest_buffered(self, timestamp: datetime) -> Optional[BufferedFrame]:
        target = _naive(timestamp)
        with self._lock:
            if not self._frames:
                return None
            best: Optional[BufferedFrame] = None
            best_delta = float("inf")
            for bf in self._frames:
                delta = abs((bf.timestamp - target).total_seconds())
                if delta < best_delta:
                    best_delta = delta
                    best = bf
            return best

    @property
    def size(self) -> int:
        return len(self._frames)

    def clear(self) -> None:
        with self._lock:
            self._frames.clear()
            self._frame_counter = 0


class FrameBufferManager:
    """Quản lý evidence frame buffer theo camera."""

    def __init__(self, seconds: float, fps: int) -> None:
        self._seconds = seconds
        self._fps = fps
        self._buffers: Dict[int, EvidenceFrameBuffer] = {}
        self._lock = threading.RLock()

    def buffer(self, camera_id: int) -> EvidenceFrameBuffer:
        with self._lock:
            buf = self._buffers.get(camera_id)
            if buf is None:
                buf = EvidenceFrameBuffer(self._seconds, self._fps)
                self._buffers[camera_id] = buf
            return buf

    def push(
        self,
        camera_id: int,
        frame: np.ndarray,
        timestamp: Optional[datetime] = None,
        frame_index: Optional[int] = None,
    ) -> int:
        return self.buffer(camera_id).push(frame, timestamp, frame_index)

    def latest(self, camera_id: int) -> Optional[np.ndarray]:
        with self._lock:
            buf = self._buffers.get(camera_id)
        return buf.latest() if buf else None

    def get_frame(self, camera_id: int, timestamp: datetime) -> Optional[np.ndarray]:
        return self.buffer(camera_id).get_frame(timestamp)

    def get_snapshot(self, camera_id: int, timestamp: datetime) -> Optional[np.ndarray]:
        return self.buffer(camera_id).get_snapshot(timestamp)

    def get_video(
        self, camera_id: int, start: datetime, end: datetime
    ) -> List[np.ndarray]:
        return self.buffer(camera_id).get_video(start, end)

    def stats(self) -> dict:
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
