"""
BenchmarkService — đo hiệu năng inference (FPS, thời gian, CPU/GPU/VRAM).
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np
from loguru import logger

from app.modules.ai.benchmark.system_metrics import read_cpu_memory, read_gpu_metrics
from app.modules.ai.exceptions import ModelNotLoadedError
from app.modules.ai.models import BenchmarkResult
from app.modules.ai.services.detection_service import DetectionService


class BenchmarkService:
    """
    Chạy benchmark trên DetectionService với ảnh ngẫu nhiên.
    """

    def __init__(self, detection_service: DetectionService) -> None:
        self._service = detection_service

    def run(
        self,
        runs: int = 50,
        image_size: Optional[int] = None,
        warmup: int = 5,
    ) -> BenchmarkResult:
        """
        Benchmark inference tốc độ.

        Args:
            runs: Số lần inference đo.
            image_size: Kích thước ảnh test (mặc định theo config model).
            warmup: Số lần chạy trước khi đo (loại nhiễu khởi động).

        Returns:
            BenchmarkResult.

        Raises:
            ModelNotLoadedError: Chưa load model.
        """
        loader = self._service.loader
        if not loader.is_loaded:
            raise ModelNotLoadedError()

        size = image_size or loader.image_size
        # Ảnh ngẫu nhiên (không phân tích nội dung, chỉ đo tốc độ)
        dummy = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)

        # Warmup
        for _ in range(max(0, warmup)):
            self._service.engine.infer(dummy, camera_id=0, frame_id=0)

        # Reset đồng hồ CPU cho psutil (lần gọi đầu trả 0)
        read_cpu_memory()

        times_ms: list[float] = []
        for i in range(runs):
            start = time.perf_counter()
            self._service.engine.infer(dummy, camera_id=0, frame_id=i)
            times_ms.append((time.perf_counter() - start) * 1000.0)

        cpu, mem = read_cpu_memory()
        gpu, vram = read_gpu_metrics()

        avg = sum(times_ms) / len(times_ms) if times_ms else 0.0
        fps = 1000.0 / avg if avg > 0 else 0.0
        info = loader.get_info()

        result = BenchmarkResult(
            model_name=info.name,
            device=info.device,
            runs=runs,
            image_size=size,
            avg_inference_ms=avg,
            min_inference_ms=min(times_ms) if times_ms else 0.0,
            max_inference_ms=max(times_ms) if times_ms else 0.0,
            fps=fps,
            cpu_percent=cpu,
            memory_mb=mem,
            gpu_percent=gpu,
            vram_mb=vram,
        )
        logger.info(
            "Benchmark done | model={} avg_ms={:.2f} fps={:.1f}",
            info.name,
            avg,
            fps,
        )
        return result
