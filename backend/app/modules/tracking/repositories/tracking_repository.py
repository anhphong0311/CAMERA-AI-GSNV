"""
InMemoryTrackingRepository — lưu TrackingResult gần đây theo camera (KHÔNG DB).

Repository Pattern trừu tượng hóa nơi lưu kết quả tracking. Sprint 4 chỉ
lưu in-memory (bounded). Không ghi database, không alert.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Dict, List, Optional

from app.modules.tracking.models import TrackingResult


class InMemoryTrackingRepository:
    """Kho lưu TrackingResult gần đây (bounded ring buffer mỗi camera)."""

    def __init__(self, max_history_per_camera: int = 200) -> None:
        self._max = max_history_per_camera
        self._latest: Dict[int, TrackingResult] = {}
        self._history: Dict[int, Deque[TrackingResult]] = {}
        self._lock = threading.RLock()

    def save(self, result: TrackingResult) -> None:
        """Lưu kết quả mới nhất + đẩy vào history."""
        with self._lock:
            self._latest[result.camera_id] = result
            buf = self._history.setdefault(result.camera_id, deque(maxlen=self._max))
            buf.append(result)

    def get_latest(self, camera_id: int) -> Optional[TrackingResult]:
        """Lấy kết quả mới nhất của camera."""
        with self._lock:
            return self._latest.get(camera_id)

    def get_all_latest(self) -> List[TrackingResult]:
        """Kết quả mới nhất của tất cả camera (live)."""
        with self._lock:
            return list(self._latest.values())

    def get_history(self, camera_id: int) -> List[TrackingResult]:
        """Lịch sử TrackingResult của camera."""
        with self._lock:
            return list(self._history.get(camera_id, deque()))

    def camera_ids(self) -> List[int]:
        """Danh sách camera đã có dữ liệu."""
        with self._lock:
            return list(self._latest.keys())
