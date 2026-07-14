"""
BaseTracker — interface thuật toán tracking (Dependency Inversion).

Cho phép thay ByteTrack → DeepSORT/OCSORT/StrongSORT mà KHÔNG đổi
TrackManager/TrackingEngine/Service/API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class DetectionInput:
    """Đầu vào tracker chuẩn hóa (tách khỏi DTO của Detection Engine)."""

    xyxy: Tuple[float, float, float, float]
    score: float
    class_id: int
    class_name: str


class BaseTracker(ABC):
    """Interface tracker — nhận detections một frame, trả TrackedObject."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên thuật toán."""

    @abstractmethod
    def update(self, detections: Sequence[DetectionInput]) -> List:
        """
        Cập nhật tracker với detections của một frame.

        Returns:
            List[TrackedObject].
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset toàn bộ trạng thái tracker."""
