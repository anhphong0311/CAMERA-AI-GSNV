"""Unit test — Compare benchmark (graceful failure without GPU/models)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.modules.performance.benchmark.compare import CompareBenchmarkService
from app.modules.performance.config.loader import PerformanceConfig


def test_benchmark_returns_all_backends():
    det = MagicMock()
    det.image_size = 640
    det.device = "cpu"
    det.model.path = "models/missing.pt"
    det.allowed_class_ids.return_value = [0]
    det.min_confidence.return_value = 0.25
    det.nms_iou = 0.45

    svc = CompareBenchmarkService(PerformanceConfig(), det)
    result = svc.run(backends=["pytorch", "onnx", "tensorrt"], runs=5, warmup=0, image_size=64)
    assert len(result["results"]) == 3
    assert "comparison" in result
    assert result["best_backend"] is None or isinstance(result["best_backend"], str)
