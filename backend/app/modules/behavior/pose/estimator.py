"""
PoseEstimator — interface pose estimation (Dependency Inversion).

Cho phép đổi YOLO Pose ↔ MediaPipe Pose mà KHÔNG đổi feature extractors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import numpy as np

from app.modules.behavior.models import PoseResult


class PoseEstimator(ABC):
    """Interface pose estimation — frame → danh sách PoseResult (người)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên model pose."""

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Đã load model chưa."""

    @abstractmethod
    def load(self) -> None:
        """Nạp model + warmup."""

    @abstractmethod
    def estimate(self, frame: np.ndarray) -> List[PoseResult]:
        """
        Ước lượng pose trên một frame.

        Args:
            frame: Ảnh BGR.

        Returns:
            List[PoseResult] cho từng người.
        """

    @abstractmethod
    def release(self) -> None:
        """Giải phóng model."""
