"""
BehaviorRepository — lưu trữ in-memory (KHÔNG database) kết quả behavior.

Phục vụ API live / track / statistics. Bounded để chống rò rỉ bộ nhớ.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from app.modules.behavior.models import BehaviorFeatureDTO, BehaviorResult


class BehaviorRepository:
    """Kho in-memory cho kết quả behavior theo camera + track."""

    def __init__(self, history_size: int = 200) -> None:
        self._lock = threading.RLock()
        self._latest_by_camera: Dict[int, BehaviorResult] = {}
        self._history: Dict[int, Deque[BehaviorResult]] = {}
        self._latest_track: Dict[int, Tuple[int, BehaviorFeatureDTO]] = {}
        self._history_size = history_size
        self._frames_processed = 0
        self._features_extracted = 0

    def save(self, result: BehaviorResult) -> None:
        """Lưu kết quả một frame."""
        with self._lock:
            self._latest_by_camera[result.camera_id] = result
            hist = self._history.setdefault(
                result.camera_id, deque(maxlen=self._history_size)
            )
            hist.append(result)
            self._frames_processed += 1
            self._features_extracted += result.count
            for f in result.features:
                self._latest_track[f.track_id] = (result.camera_id, f)

    def get_live(self) -> List[BehaviorResult]:
        """Kết quả mới nhất của tất cả camera."""
        with self._lock:
            return list(self._latest_by_camera.values())

    def get_camera(self, camera_id: int) -> Optional[BehaviorResult]:
        """Kết quả mới nhất của một camera."""
        with self._lock:
            return self._latest_by_camera.get(camera_id)

    def get_track(
        self, track_id: int
    ) -> Optional[Tuple[int, BehaviorFeatureDTO]]:
        """Đặc trưng mới nhất của một track (kèm camera_id)."""
        with self._lock:
            return self._latest_track.get(track_id)

    def statistics(self) -> dict:
        """Thống kê tổng hợp."""
        with self._lock:
            per_camera = {
                cam: res.count for cam, res in self._latest_by_camera.items()
            }
            return {
                "frames_processed": self._frames_processed,
                "features_extracted": self._features_extracted,
                "active_cameras": len(self._latest_by_camera),
                "tracked": len(self._latest_track),
                "per_camera_count": per_camera,
            }

    def clear(self) -> None:
        """Xóa toàn bộ."""
        with self._lock:
            self._latest_by_camera.clear()
            self._history.clear()
            self._latest_track.clear()
            self._frames_processed = 0
            self._features_extracted = 0
