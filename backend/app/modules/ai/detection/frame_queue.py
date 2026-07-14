"""
AIFrameQueue — hàng đợi frame bounded, thread-safe, drop-oldest.

Mỗi camera có một queue riêng trong DetectionPipeline để không camera nào
block camera khác. Độc lập với FrameBuffer của Camera Service (Sprint 2).
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Optional

import numpy as np

from app.modules.ai.models import utc_now


@dataclass
class QueuedFrame:
    """Một frame chờ inference."""

    camera_id: int
    frame_id: int
    frame: np.ndarray
    enqueued_at: datetime


class AIFrameQueue:
    """
    Bounded queue drop-oldest cho một camera.

    Khi đầy → loại frame cũ nhất (ưu tiên realtime), tăng dropped_count.
    """

    def __init__(self, camera_id: int, max_size: int = 5) -> None:
        self.camera_id = camera_id
        self._max_size = max_size
        self._deque: Deque[QueuedFrame] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self.dropped_count = 0

    @property
    def size(self) -> int:
        """Số frame trong queue."""
        with self._lock:
            return len(self._deque)

    def put(self, frame_id: int, frame: np.ndarray) -> None:
        """
        Đẩy frame vào queue (non-blocking, drop-oldest khi đầy).

        Args:
            frame_id: Số thứ tự frame.
            frame: Ảnh BGR.
        """
        with self._lock:
            if len(self._deque) >= self._max_size:
                self.dropped_count += 1
            self._deque.append(
                QueuedFrame(
                    camera_id=self.camera_id,
                    frame_id=frame_id,
                    frame=frame,
                    enqueued_at=utc_now(),
                )
            )

    def get(self) -> Optional[QueuedFrame]:
        """
        Lấy frame cũ nhất (FIFO).

        Returns:
            QueuedFrame hoặc None nếu rỗng.
        """
        with self._lock:
            if not self._deque:
                return None
            return self._deque.popleft()

    def clear(self) -> None:
        """Xóa toàn bộ queue."""
        with self._lock:
            self._deque.clear()
