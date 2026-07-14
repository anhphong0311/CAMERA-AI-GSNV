"""
DTO — BenchmarkResult: kết quả đo hiệu năng inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkResult:
    """
    Kết quả benchmark Detection Engine.

    Attributes:
        model_name: Model đã benchmark.
        device: Thiết bị chạy.
        runs: Số lần inference đo.
        image_size: Kích thước ảnh test.
        avg_inference_ms: Thời gian inference trung bình.
        min_inference_ms / max_inference_ms: Biên.
        fps: FPS trung bình.
        cpu_percent: % CPU trong quá trình benchmark.
        memory_mb: RAM tiến trình (MB).
        gpu_percent: % GPU (None nếu không có).
        vram_mb: VRAM sử dụng (MB, None nếu không có).
    """

    model_name: str
    device: str
    runs: int
    image_size: int
    avg_inference_ms: float
    min_inference_ms: float
    max_inference_ms: float
    fps: float
    cpu_percent: float | None = None
    memory_mb: float | None = None
    gpu_percent: float | None = None
    vram_mb: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize cho API response."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "runs": self.runs,
            "image_size": self.image_size,
            "avg_inference_ms": round(self.avg_inference_ms, 2),
            "min_inference_ms": round(self.min_inference_ms, 2),
            "max_inference_ms": round(self.max_inference_ms, 2),
            "fps": round(self.fps, 2),
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "gpu_percent": self.gpu_percent,
            "vram_mb": self.vram_mb,
        }
