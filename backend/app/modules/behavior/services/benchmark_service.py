"""
BenchmarkService — đo hiệu năng Behavior Engine (Pose FPS/Latency/CPU/GPU/VRAM).

Sinh dữ liệu tổng hợp (track + skeleton) để chạy pipeline không cần camera thật.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

import numpy as np

from app.modules.behavior.config import BehaviorConfig, load_behavior_config
from app.modules.behavior.feature_engine import BehaviorFeatureEngine
from app.modules.behavior.models import Keypoints, PoseResult


@dataclass
class _FakeTrack:
    """Track tối thiểu (duck-typed) cho benchmark."""

    track_id: int
    camera_id: int
    bbox: Tuple[float, float, float, float]
    speed_px: float = 1.0
    direction: str = "RIGHT"
    current_roi_id: Optional[str] = None

    @property
    def center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


@dataclass
class _FakeTrackingResult:
    """TrackingResult tối thiểu cho benchmark."""

    camera_id: int
    frame_id: int
    timestamp: datetime
    tracks: List[_FakeTrack] = field(default_factory=list)


@dataclass
class BehaviorBenchmarkResult:
    """Kết quả benchmark Behavior Engine."""

    frames: int
    people: int
    used_real_pose: bool
    avg_latency_ms: float
    p95_latency_ms: float
    fps: float
    cpu_percent: float
    memory_mb: float
    gpu_percent: Optional[float]
    vram_mb: Optional[float]

    def to_dict(self) -> dict[str, Any]:
        """Serialize."""
        return {
            "frames": self.frames,
            "people": self.people,
            "used_real_pose": self.used_real_pose,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "fps": round(self.fps, 2),
            "cpu_percent": round(self.cpu_percent, 1),
            "memory_mb": round(self.memory_mb, 1),
            "gpu_percent": round(self.gpu_percent, 1)
            if self.gpu_percent is not None
            else None,
            "vram_mb": round(self.vram_mb, 1) if self.vram_mb is not None else None,
        }


def _synthetic_skeleton(bbox: Tuple[float, float, float, float]) -> Keypoints:
    """Tạo skeleton COCO-17 hợp lý bên trong bbox (đứng)."""
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    cx = (x1 + x2) / 2.0

    def p(dx_ratio: float, dy_ratio: float) -> Tuple[float, float, float]:
        return (cx + dx_ratio * w, y1 + dy_ratio * h, 0.9)

    points = [
        p(0.0, 0.12),   # nose
        p(-0.05, 0.10), # left_eye
        p(0.05, 0.10),  # right_eye
        p(-0.08, 0.11), # left_ear
        p(0.08, 0.11),  # right_ear
        p(-0.18, 0.25), # left_shoulder
        p(0.18, 0.25),  # right_shoulder
        p(-0.20, 0.42), # left_elbow
        p(0.20, 0.42),  # right_elbow
        p(-0.18, 0.58), # left_wrist
        p(0.18, 0.58),  # right_wrist
        p(-0.12, 0.55), # left_hip
        p(0.12, 0.55),  # right_hip
        p(-0.12, 0.78), # left_knee
        p(0.12, 0.78),  # right_knee
        p(-0.12, 0.98), # left_ankle
        p(0.12, 0.98),  # right_ankle
    ]
    return Keypoints(points, 0.3)


class BenchmarkService:
    """Benchmark Behavior Feature Engine."""

    def __init__(self, config: Optional[BehaviorConfig] = None, pose=None) -> None:
        self._config = config or load_behavior_config()
        self._pose = pose

    def run(
        self,
        frames: int = 120,
        people: int = 20,
        width: int = 1280,
        height: int = 720,
        use_real_pose: bool = False,
    ) -> BehaviorBenchmarkResult:
        """
        Chạy benchmark.

        Args:
            frames: Số frame mô phỏng.
            people: Số người.
            width/height: Kích thước frame.
            use_real_pose: True → chạy pose model thật (nếu đã load).

        Returns:
            BehaviorBenchmarkResult.
        """
        from app.modules.ai.benchmark.system_metrics import (
            read_cpu_memory,
            read_gpu_metrics,
        )

        engine = BehaviorFeatureEngine(camera_id=1, config=self._config)
        use_real = bool(
            use_real_pose and self._pose is not None and self._pose.is_loaded
        )
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        latencies: List[float] = []
        for f in range(frames):
            offset = (f * 3) % max(1, (width - 120))
            tracks: List[_FakeTrack] = []
            poses: List[PoseResult] = []
            for pid in range(people):
                bx = 20 + offset + (pid % 10) * 100
                by = 40 + (pid // 10) * 260
                bbox = (float(bx), float(by), float(bx + 80), float(by + 220))
                tracks.append(
                    _FakeTrack(track_id=pid + 1, camera_id=1, bbox=bbox, speed_px=3.0)
                )
                if not use_real:
                    poses.append(
                        PoseResult(bbox=bbox, score=0.9, keypoints=_synthetic_skeleton(bbox))
                    )
            tr = _FakeTrackingResult(
                camera_id=1,
                frame_id=f,
                timestamp=datetime.now(timezone.utc),
                tracks=tracks,
            )

            t0 = time.perf_counter()
            if use_real:
                real_poses = self._pose.estimate(frame)
                engine.process(tr, real_poses, None)
            else:
                engine.process(tr, poses, None)
            latencies.append((time.perf_counter() - t0) * 1000.0)

        cpu, mem = read_cpu_memory()
        gpu, vram = read_gpu_metrics()
        cpu = cpu if cpu is not None else 0.0
        mem = mem if mem is not None else 0.0
        latencies.sort()
        avg = sum(latencies) / len(latencies) if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        fps = 1000.0 / avg if avg > 0 else 0.0

        return BehaviorBenchmarkResult(
            frames=frames,
            people=people,
            used_real_pose=use_real,
            avg_latency_ms=avg,
            p95_latency_ms=p95,
            fps=fps,
            cpu_percent=cpu,
            memory_mb=mem,
            gpu_percent=gpu,
            vram_mb=vram,
        )
