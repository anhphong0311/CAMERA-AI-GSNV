"""
Unit tests — BenchmarkService (với FakeBackend, không cần GPU).
"""

import pytest

from app.modules.ai.models import RawDetection
from app.modules.ai.services.benchmark_service import BenchmarkService
from app.modules.ai.services.detection_service import DetectionService

from tests.modules.ai.conftest import FakeBackend


class TestBenchmarkService:
    """Test benchmark hiệu năng."""

    def _service_with_fake(self, config) -> DetectionService:
        service = DetectionService(config)
        # Inject backend giả để bỏ qua load model thật
        service.loader._backend = FakeBackend([RawDetection(0, 0.9, (0, 0, 10, 10))])
        service.loader._info.loaded = True
        return service

    def test_benchmark_returns_result(self, detection_config) -> None:
        """Benchmark trả FPS/thời gian hợp lệ."""
        service = self._service_with_fake(detection_config)
        bench = BenchmarkService(service)
        result = bench.run(runs=5, image_size=320, warmup=1)
        assert result.runs == 5
        assert result.image_size == 320
        assert result.avg_inference_ms >= 0
        assert result.fps >= 0
        assert result.min_inference_ms <= result.max_inference_ms

    def test_benchmark_requires_loaded_model(self, detection_config) -> None:
        """Chưa load model → ModelNotLoadedError."""
        from app.modules.ai.exceptions import ModelNotLoadedError

        service = DetectionService(detection_config)
        bench = BenchmarkService(service)
        with pytest.raises(ModelNotLoadedError):
            bench.run(runs=2)
