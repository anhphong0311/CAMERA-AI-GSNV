"""
BenchmarkService — đo hiệu năng & độ ổn định tracking.

Sinh DetectionResult giả (N người di chuyển) rồi chạy tracking, đo:
FPS, track count, ID switch (xấp xỉ), stability, recovery, lost, CPU, memory.
KHÔNG chạy AI/model.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, List

from loguru import logger

from app.modules.ai.benchmark.system_metrics import read_cpu_memory, read_gpu_metrics
from app.modules.ai.models import BoundingBox, Detection, DetectionResult, utc_now
from app.modules.tracking.config import TrackingConfig
from app.modules.tracking.tracking_engine.engine import TrackingEngine


@dataclass
class TrackingBenchmarkResult:
    """Kết quả benchmark tracking."""

    tracker: str
    frames: int
    num_people: int
    avg_processing_ms: float
    fps: float
    final_active_tracks: int
    total_created: int
    id_switches: int
    track_stability: float
    total_lost: int
    total_recovered: int
    cpu_percent: float | None = None
    memory_mb: float | None = None
    gpu_percent: float | None = None
    vram_mb: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize cho API."""
        return {
            "tracker": self.tracker,
            "frames": self.frames,
            "num_people": self.num_people,
            "avg_processing_ms": round(self.avg_processing_ms, 3),
            "fps": round(self.fps, 2),
            "final_active_tracks": self.final_active_tracks,
            "total_created": self.total_created,
            "id_switches": self.id_switches,
            "track_stability": round(self.track_stability, 3),
            "total_lost": self.total_lost,
            "total_recovered": self.total_recovered,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "gpu_percent": self.gpu_percent,
            "vram_mb": self.vram_mb,
        }


class BenchmarkService:
    """Chạy benchmark tracking với dữ liệu tổng hợp."""

    def __init__(self, config: TrackingConfig) -> None:
        self._config = config

    def run(
        self,
        frames: int = 100,
        num_people: int = 20,
        width: int = 1280,
        height: int = 720,
    ) -> TrackingBenchmarkResult:
        """
        Benchmark tracking N người qua M frame.

        Args:
            frames: Số frame mô phỏng.
            num_people: Số người (mục tiêu >= 20).
            width, height: Kích thước khung hình.

        Returns:
            TrackingBenchmarkResult.
        """
        engine = TrackingEngine(camera_id=0, config=self._config, roi_configs=[])
        box_w, box_h = 40.0, 100.0
        base_time = utc_now()
        read_cpu_memory()  # reset đồng hồ CPU

        times_ms: List[float] = []
        for f in range(frames):
            objects: List[Detection] = []
            for pid in range(num_people):
                # Mỗi người di chuyển ngang đều, lệch theo pid
                x = (pid * 55 + f * 3) % (width - box_w)
                y = (pid * 30) % (height - box_h)
                objects.append(
                    Detection(
                        class_name="person",
                        confidence=0.9,
                        bbox=BoundingBox(x, y, x + box_w, y + box_h),
                        class_id=0,
                    )
                )
            detection = DetectionResult(
                camera_id=0,
                frame_id=f,
                timestamp=base_time + timedelta(seconds=f / 30.0),
                objects=objects,
                width=width,
                height=height,
            )
            start = time.perf_counter()
            engine.update(detection)
            times_ms.append((time.perf_counter() - start) * 1000.0)

        stats = engine.statistics()
        cpu, mem = read_cpu_memory()
        gpu, vram = read_gpu_metrics()

        avg = sum(times_ms) / len(times_ms) if times_ms else 0.0
        fps = 1000.0 / avg if avg > 0 else 0.0
        total_created = stats["total_created"]
        id_switches = max(0, total_created - num_people)
        stability = num_people / total_created if total_created else 0.0

        result = TrackingBenchmarkResult(
            tracker=stats.get("tracker", "bytetrack"),
            frames=frames,
            num_people=num_people,
            avg_processing_ms=avg,
            fps=fps,
            final_active_tracks=stats["active_tracks"],
            total_created=total_created,
            id_switches=id_switches,
            track_stability=stability,
            total_lost=stats["total_lost"],
            total_recovered=stats["total_recovered"],
            cpu_percent=cpu,
            memory_mb=mem,
            gpu_percent=gpu,
            vram_mb=vram,
        )
        logger.info(
            "Tracking benchmark | fps={:.1f} people={} created={} id_switch={}",
            fps,
            num_people,
            total_created,
            id_switches,
        )
        return result
