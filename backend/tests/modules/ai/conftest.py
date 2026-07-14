"""
Fixtures dùng chung cho test AI Detection Engine.

FakeBackend cho phép test toàn bộ pipeline mà KHÔNG cần cài torch/ultralytics.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np
import pytest

from app.modules.ai.config import ClassConfig, DetectionConfig, ModelConfig, QueueConfig
from app.modules.ai.inference.backend import InferenceBackend
from app.modules.ai.models import RawDetection


class FakeBackend(InferenceBackend):
    """Backend giả trả detection cố định — không phụ thuộc GPU/torch."""

    def __init__(self, detections: Sequence[RawDetection] | None = None) -> None:
        self._dets = list(detections or [])
        self.predict_calls = 0
        self.warmup_calls = 0
        self.released = False

    @property
    def device(self) -> str:
        return "cpu"

    @property
    def class_names(self) -> dict[int, str]:
        return {0: "person", 39: "bottle", 41: "cup", 67: "cell phone"}

    def predict(
        self,
        frame: np.ndarray,
        image_size: int,
        confidence: float,
        iou: float,
        allowed_class_ids: Sequence[int],
        half: bool,
    ) -> List[RawDetection]:
        self.predict_calls += 1
        return list(self._dets)

    def warmup(self, image_size: int, iterations: int = 3) -> None:
        self.warmup_calls += 1

    def release(self) -> None:
        self.released = True


@pytest.fixture
def detection_config() -> DetectionConfig:
    """DetectionConfig tối giản dùng cho test (device cpu)."""
    return DetectionConfig(
        model=ModelConfig(path="yolo11n.pt", name="yolo11n"),
        device="cpu",
        half_precision=False,
        image_size=640,
        nms_iou=0.45,
        max_detections=100,
        default_confidence=0.5,
        auto_load=False,
        warmup_iterations=1,
        classes={
            "person": ClassConfig(ids=[0], confidence=0.50),
            "phone": ClassConfig(ids=[67], confidence=0.65),
            "cup": ClassConfig(ids=[41], confidence=0.50),
            "bottle": ClassConfig(ids=[39], confidence=0.50),
            "monitor": ClassConfig(ids=[62], confidence=0.50),
        },
        queue=QueueConfig(max_size=3, num_workers=2, poll_interval_ms=2),
    )


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Frame BGR 480x640 giả (không phân tích nội dung)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)
