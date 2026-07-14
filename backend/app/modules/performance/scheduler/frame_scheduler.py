"""
Frame Scheduler (Sprint 10) — skip frame, adaptive FPS, priority.

Camera 30 FPS → AI xử lý ~10 FPS; tracking vẫn mượt vì dùng kết quả mới nhất.
Thread-safe, không global state.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.modules.performance.config.loader import FrameSchedulerConfig


@dataclass
class CameraFrameStats:
    """Thống kê frame theo camera."""

    camera_id: int
    capture_fps: float = 0.0
    ai_fps: float = 0.0
    skipped: int = 0
    processed: int = 0
    last_capture_ts: float = 0.0
    last_process_ts: float = 0.0


class FrameScheduler:
    """
    Quyết định frame nào được đưa vào AI pipeline.

    Modes:
    - adaptive: duy trì target_ai_fps dựa trên thời gian thực
    - fixed: skip theo tỷ lệ max_capture/target_ai
    - priority: camera ưu tiên luôn xử lý
    """

    def __init__(self, config: FrameSchedulerConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._stats: Dict[int, CameraFrameStats] = {}
        self._skip_ratio = max(1, int(config.max_capture_fps / max(config.target_ai_fps, 1)))
        self._frame_counters: Dict[int, int] = field(default_factory=dict)  # type: ignore[assignment]
        self._frame_counters = {}

    def should_process(self, camera_id: int, *, priority: bool = False) -> bool:
        """Trả True nếu frame này nên inference."""
        if not self._config.enabled:
            return True

        now = time.monotonic()
        with self._lock:
            stats = self._stats.setdefault(camera_id, CameraFrameStats(camera_id=camera_id))
            stats.last_capture_ts = now

            if priority or camera_id in self._config.priority_cameras:
                stats.processed += 1
                stats.last_process_ts = now
                self._update_fps(stats, now)
                return True

            mode = self._config.skip_mode
            if mode == "fixed":
                cnt = self._frame_counters.get(camera_id, 0) + 1
                self._frame_counters[camera_id] = cnt
                if cnt % self._skip_ratio != 0:
                    stats.skipped += 1
                    return False
                stats.processed += 1
                stats.last_process_ts = now
                self._update_fps(stats, now)
                return True

            if mode == "adaptive":
                min_interval = 1.0 / self._config.target_ai_fps
                if stats.last_process_ts > 0 and (now - stats.last_process_ts) < min_interval:
                    stats.skipped += 1
                    return False
                stats.processed += 1
                stats.last_process_ts = now
                self._update_fps(stats, now)
                return True

            # priority mode without being in list → adaptive
            min_interval = 1.0 / self._config.target_ai_fps
            if stats.last_process_ts > 0 and (now - stats.last_process_ts) < min_interval:
                stats.skipped += 1
                return False
            stats.processed += 1
            stats.last_process_ts = now
            self._update_fps(stats, now)
            return True

    @staticmethod
    def _update_fps(stats: CameraFrameStats, now: float) -> None:
        if stats.last_process_ts > 0:
            dt = now - stats.last_process_ts
            if dt > 0:
                stats.ai_fps = round(1.0 / dt, 1)

    def stats(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "camera_id": s.camera_id,
                    "capture_fps": s.capture_fps,
                    "ai_fps": s.ai_fps,
                    "skipped": s.skipped,
                    "processed": s.processed,
                    "skip_ratio": self._skip_ratio,
                }
                for s in self._stats.values()
            ]

    def summary(self) -> dict:
        rows = self.stats()
        total_skipped = sum(r["skipped"] for r in rows)
        total_processed = sum(r["processed"] for r in rows)
        return {
            "enabled": self._config.enabled,
            "target_ai_fps": self._config.target_ai_fps,
            "max_capture_fps": self._config.max_capture_fps,
            "skip_mode": self._config.skip_mode,
            "total_skipped": total_skipped,
            "total_processed": total_processed,
            "cameras": rows,
        }
