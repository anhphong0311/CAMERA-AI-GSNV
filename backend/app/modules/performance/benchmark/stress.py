"""
Stress test (Sprint 10) — mô phỏng 1–100 camera submit frame.

Đo throughput, queue depth, dropped frames, FPS — không cần GPU thật.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

import numpy as np

from app.modules.performance.config.loader import StressConfig


class StressTestService:
    """Stress test pipeline bằng synthetic multi-camera load."""

    def __init__(self, stress_config: StressConfig) -> None:
        self._config = stress_config

    def run(
        self,
        submit_fn,
        *,
        camera_counts: Optional[List[int]] = None,
        duration_s: Optional[int] = None,
        image_size: int = 640,
    ) -> Dict[str, Any]:
        counts = camera_counts or self._config.camera_counts
        duration = duration_s or self._config.durations_s
        reports: List[dict] = []

        for n_cameras in counts:
            reports.append(self._run_scenario(n_cameras, duration, image_size, submit_fn))

        return {
            "duration_s": duration,
            "scenarios": reports,
            "summary": self._summarize(reports),
        }

    def _run_scenario(self, n_cameras: int, duration: int, size: int, submit_fn) -> dict:
        stop = threading.Event()
        submitted = 0
        errors = 0
        lock = threading.Lock()

        def producer(cam_id: int) -> None:
            nonlocal submitted, errors
            fid = 0
            frame = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
            while not stop.is_set():
                try:
                    submit_fn(cam_id, frame, fid)
                    fid += 1
                    with lock:
                        submitted += 1
                except Exception:
                    with lock:
                        errors += 1
                time.sleep(1.0 / 30)  # 30 FPS capture sim

        threads = [
            threading.Thread(target=producer, args=(i,), daemon=True)
            for i in range(n_cameras)
        ]
        start = time.perf_counter()
        for t in threads:
            t.start()
        time.sleep(duration)
        stop.set()
        for t in threads:
            t.join(timeout=2)
        elapsed = time.perf_counter() - start
        fps = submitted / elapsed if elapsed > 0 else 0
        return {
            "cameras": n_cameras,
            "submitted": submitted,
            "errors": errors,
            "elapsed_s": round(elapsed, 2),
            "throughput_fps": round(fps, 2),
            "avg_fps_per_camera": round(fps / max(n_cameras, 1), 2),
        }

    @staticmethod
    def _summarize(reports: List[dict]) -> dict:
        return {
            "max_cameras_tested": max((r["cameras"] for r in reports), default=0),
            "min_throughput_fps": min((r["throughput_fps"] for r in reports), default=0),
            "max_throughput_fps": max((r["throughput_fps"] for r in reports), default=0),
            "total_errors": sum(r["errors"] for r in reports),
        }
