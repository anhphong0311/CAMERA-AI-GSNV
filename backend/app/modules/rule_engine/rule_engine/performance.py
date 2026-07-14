"""
PerformanceScore — tính điểm hiệu suất từ thời gian các nhóm hành vi.

Rule Engine tự tính (Sprint 6 yêu cầu): Working/Phone/Talking/Eating/Sleeping/
Away/Idle time → Performance Score (0..100).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TrackPerformance:
    """Tích lũy thời gian hành vi cho một track."""

    track_id: int
    camera_id: int
    total_time: float = 0.0
    working_time: float = 0.0
    category_time: Dict[str, float] = field(
        default_factory=lambda: {
            "phone": 0.0,
            "talking": 0.0,
            "eating": 0.0,
            "sleeping": 0.0,
            "away": 0.0,
            "idle": 0.0,
        }
    )


class PerformanceScoreCalculator:
    """Tính và lưu điểm hiệu suất theo track."""

    def __init__(self, weights: Dict[str, float]) -> None:
        self._weights = weights
        self._tracks: Dict[int, TrackPerformance] = {}
        self._lock = threading.RLock()

    def update(
        self,
        track_id: int,
        camera_id: int,
        dt: float,
        active_categories: Dict[str, bool],
        working: bool,
    ) -> None:
        """Cập nhật tích lũy cho một track theo dt (giây)."""
        if dt <= 0:
            return
        with self._lock:
            perf = self._tracks.get(track_id)
            if perf is None:
                perf = TrackPerformance(track_id=track_id, camera_id=camera_id)
                self._tracks[track_id] = perf
            perf.total_time += dt
            if working:
                perf.working_time += dt
            for cat, active in active_categories.items():
                if active and cat in perf.category_time:
                    perf.category_time[cat] += dt

    def score(self, track_id: int) -> float:
        """
        Điểm hiệu suất 0..100 cho một track.

        score = 100 - Σ weight[cat] * (cat_time/total)*100, kẹp trong [0,100].
        """
        with self._lock:
            perf = self._tracks.get(track_id)
            if perf is None or perf.total_time <= 0:
                return 100.0
            penalty = 0.0
            for cat, seconds in perf.category_time.items():
                ratio = seconds / perf.total_time
                penalty += self._weights.get(cat, 1.0) * ratio * 100.0
            return round(max(0.0, min(100.0, 100.0 - penalty)), 1)

    def report(self, track_id: int) -> Dict[str, Any]:
        """Báo cáo chi tiết cho một track."""
        with self._lock:
            perf = self._tracks.get(track_id)
            if perf is None:
                return {"track_id": track_id, "score": 100.0, "total_time": 0.0}
            return {
                "track_id": track_id,
                "camera_id": perf.camera_id,
                "score": self.score(track_id),
                "total_time": round(perf.total_time, 1),
                "working_time": round(perf.working_time, 1),
                "category_time": {
                    k: round(v, 1) for k, v in perf.category_time.items()
                },
            }

    def all_reports(self) -> List[Dict[str, Any]]:
        """Báo cáo toàn bộ track."""
        with self._lock:
            return [self.report(tid) for tid in self._tracks]

    def clear(self) -> None:
        with self._lock:
            self._tracks.clear()
