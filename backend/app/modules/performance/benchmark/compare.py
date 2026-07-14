"""
Backend benchmark comparison (Sprint 10) — PyTorch vs ONNX vs TensorRT.

Đo FPS, latency, VRAM, CPU, GPU cho từng backend.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from app.modules.ai.benchmark.system_metrics import read_cpu_memory, read_gpu_metrics
from app.modules.performance.backends.factory import BackendType, create_backend
from app.modules.performance.config.loader import BenchmarkConfig, PerformanceConfig


@dataclass
class BackendBenchmarkResult:
    backend: str
    success: bool
    avg_inference_ms: float = 0.0
    min_inference_ms: float = 0.0
    max_inference_ms: float = 0.0
    fps: float = 0.0
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    gpu_percent: Optional[float] = None
    vram_mb: Optional[float] = None
    precision: str = "fp32"
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "success": self.success,
            "avg_inference_ms": round(self.avg_inference_ms, 2),
            "min_inference_ms": round(self.min_inference_ms, 2),
            "max_inference_ms": round(self.max_inference_ms, 2),
            "fps": round(self.fps, 2),
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "gpu_percent": self.gpu_percent,
            "vram_mb": self.vram_mb,
            "precision": self.precision,
            "error": self.error,
        }


class CompareBenchmarkService:
    """So sánh hiệu năng các backend inference."""

    def __init__(self, perf_config: PerformanceConfig, detection_config: Any) -> None:
        self._perf = perf_config
        self._det = detection_config

    def run(
        self,
        backends: Optional[List[str]] = None,
        runs: Optional[int] = None,
        warmup: Optional[int] = None,
        image_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        cfg: BenchmarkConfig = self._perf.benchmark
        backends = backends or cfg.backends
        runs = runs or cfg.runs
        warmup = warmup if warmup is not None else cfg.warmup
        size = image_size or self._det.image_size
        device = self._det.device if hasattr(self._det, "device") else "auto"
        from app.modules.ai.utils.device import resolve_device

        device = resolve_device(device)
        half = self._perf.backend.precision in ("fp16", "int8")
        model_path = self._det.model.path
        dummy = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
        allowed = self._det.allowed_class_ids() if hasattr(self._det, "allowed_class_ids") else list(range(80))
        conf = self._det.min_confidence() if hasattr(self._det, "min_confidence") else 0.25
        iou = getattr(self._det, "nms_iou", 0.45)

        results: List[BackendBenchmarkResult] = []
        for name in backends:
            results.append(
                self._bench_one(
                    name, dummy, size, runs, warmup, device, half,
                    model_path, conf, iou, allowed,
                )
            )

        successful = [r for r in results if r.success]
        best = max(successful, key=lambda r: r.fps, default=None)
        return {
            "runs": runs,
            "warmup": warmup,
            "image_size": size,
            "device": device,
            "precision": self._perf.backend.precision,
            "results": [r.to_dict() for r in results],
            "best_backend": best.backend if best else None,
            "comparison": self._comparison_table(results),
        }

    def _bench_one(
        self, backend_type: str, dummy, size, runs, warmup, device, half,
        model_path, conf, iou, allowed,
    ) -> BackendBenchmarkResult:
        result = BackendBenchmarkResult(
            backend=backend_type,
            success=False,
            precision=self._perf.backend.precision,
        )
        try:
            backend = create_backend(
                backend_type,  # type: ignore[arg-type]
                model_path=model_path,
                onnx_path=self._perf.backend.onnx_path,
                tensorrt_path=self._perf.backend.tensorrt_path,
                device=device,
                half=half,
                auto_export_onnx=self._perf.backend.auto_export_onnx,
                image_size=size,
            )
            for _ in range(max(0, warmup)):
                backend.predict(dummy, size, conf, iou, allowed, half)
            read_cpu_memory()
            times: List[float] = []
            for _ in range(runs):
                t0 = time.perf_counter()
                backend.predict(dummy, size, conf, iou, allowed, half)
                times.append((time.perf_counter() - t0) * 1000)
            cpu, mem = read_cpu_memory()
            gpu, vram = read_gpu_metrics()
            avg = sum(times) / len(times) if times else 0
            result.success = True
            result.avg_inference_ms = avg
            result.min_inference_ms = min(times) if times else 0
            result.max_inference_ms = max(times) if times else 0
            result.fps = 1000 / avg if avg > 0 else 0
            result.cpu_percent = cpu
            result.memory_mb = mem
            result.gpu_percent = gpu
            result.vram_mb = vram
            backend.release()
        except Exception as exc:
            result.error = str(exc)
            logger.warning("Benchmark {} failed: {}", backend_type, exc)
        return result

    @staticmethod
    def _comparison_table(results: List[BackendBenchmarkResult]) -> List[dict]:
        base_fps = next((r.fps for r in results if r.backend == "pytorch" and r.success), 0)
        table = []
        for r in results:
            speedup = round(r.fps / base_fps, 2) if base_fps > 0 and r.success else None
            table.append({"backend": r.backend, "fps": r.fps if r.success else 0, "speedup_vs_pytorch": speedup})
        return table
