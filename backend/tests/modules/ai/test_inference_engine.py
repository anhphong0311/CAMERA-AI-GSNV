"""
Unit tests — InferenceEngine (frame → DetectionResult) với FakeBackend.
"""

import numpy as np
import pytest

from app.modules.ai.exceptions import InvalidFrameError, ModelNotLoadedError
from app.modules.ai.inference.engine import InferenceEngine
from app.modules.ai.inference.model_loader import ModelLoader
from app.modules.ai.models import RawDetection
from app.modules.ai.repositories.model_repository import ModelRepository

from tests.modules.ai.conftest import FakeBackend


def _make_engine(config, backend: FakeBackend) -> InferenceEngine:
    """Tạo engine với backend giả gắn sẵn vào loader."""
    loader = ModelLoader(
        model_path=config.model.path,
        model_name=config.model.name,
        device="cpu",
        image_size=config.image_size,
        repository=ModelRepository(search_dirs=[]),
    )
    loader._backend = backend  # inject fake backend (bỏ qua load thật)
    return InferenceEngine(loader, config)


class TestInferenceEngine:
    """Test luồng inference chính."""

    def test_infer_returns_detection_result(self, detection_config, sample_frame) -> None:
        """Frame hợp lệ → DetectionResult với đúng metadata."""
        backend = FakeBackend([RawDetection(0, 0.9, (10, 10, 100, 200))])
        engine = _make_engine(detection_config, backend)
        result = engine.infer(sample_frame, camera_id=3, frame_id=7)
        assert result.camera_id == 3
        assert result.frame_id == 7
        assert result.width == 640
        assert result.height == 480
        assert result.count == 1
        assert result.objects[0].class_name == "person"
        assert result.inference_time_ms >= 0

    def test_per_class_confidence_filtering(self, detection_config, sample_frame) -> None:
        """Phone dưới ngưỡng 0.65 bị loại; person được giữ."""
        backend = FakeBackend(
            [
                RawDetection(0, 0.90, (0, 0, 50, 50)),  # person keep
                RawDetection(67, 0.60, (0, 0, 50, 50)),  # phone drop (<0.65)
            ]
        )
        engine = _make_engine(detection_config, backend)
        result = engine.infer(sample_frame)
        labels = [o.class_name for o in result.objects]
        assert "person" in labels
        assert "phone" not in labels

    def test_invalid_frame_raises(self, detection_config) -> None:
        """Frame None → InvalidFrameError."""
        backend = FakeBackend()
        engine = _make_engine(detection_config, backend)
        with pytest.raises(InvalidFrameError):
            engine.infer(None)  # type: ignore[arg-type]

    def test_model_not_loaded_raises(self, detection_config, sample_frame) -> None:
        """Backend None → ModelNotLoadedError."""
        loader = ModelLoader(
            model_path=detection_config.model.path,
            model_name=detection_config.model.name,
            device="cpu",
            repository=ModelRepository(search_dirs=[]),
        )
        engine = InferenceEngine(loader, detection_config)
        with pytest.raises(ModelNotLoadedError):
            engine.infer(sample_frame)

    def test_multiple_classes_detected(self, detection_config, sample_frame) -> None:
        """Nhiều class hợp lệ đều được nhận (person, cup, bottle, monitor)."""
        backend = FakeBackend(
            [
                RawDetection(0, 0.9, (0, 0, 50, 50)),
                RawDetection(41, 0.7, (10, 10, 60, 60)),
                RawDetection(39, 0.8, (20, 20, 70, 70)),
                RawDetection(62, 0.75, (30, 30, 90, 90)),
            ]
        )
        engine = _make_engine(detection_config, backend)
        result = engine.infer(sample_frame)
        labels = {o.class_name for o in result.objects}
        assert {"person", "cup", "bottle", "monitor"}.issubset(labels)
