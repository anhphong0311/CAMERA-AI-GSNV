"""
HeadFeatureExtractor — trích đặc trưng đầu từ keypoints (ước lượng).
"""

from __future__ import annotations

import statistics
from typing import List, Optional, Tuple

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.models import HeadFeature, Keypoints
from app.modules.behavior.models.keypoints import (
    LEFT_EAR,
    LEFT_EYE,
    LEFT_SHOULDER,
    NOSE,
    RIGHT_EAR,
    RIGHT_EYE,
    RIGHT_SHOULDER,
)
from app.modules.behavior.utils.geometry import midpoint, scale_from


class HeadFeatureExtractor:
    """Trích Head Position/Angle/Direction/Stability."""

    def __init__(self, thresholds: ThresholdConfig) -> None:
        self._t = thresholds

    def extract(
        self,
        kpts: Keypoints,
        bbox: Tuple[float, float, float, float],
        recent_angles: Optional[List[float]] = None,
    ) -> HeadFeature:
        """
        Trích đặc trưng đầu.

        Args:
            kpts: Keypoints.
            bbox: Khung người.
            recent_angles: Lịch sử góc đầu (tính độ ổn định).

        Returns:
            HeadFeature (available=False nếu thiếu joint).
        """
        nose = kpts.get(NOSE)
        ls = kpts.get(LEFT_SHOULDER)
        rs = kpts.get(RIGHT_SHOULDER)
        neck = midpoint(ls, rs)
        if nose is None or neck is None:
            return HeadFeature(available=False)

        scale = scale_from(ls, rs, bbox)
        ear_mid = midpoint(kpts.get(LEFT_EAR), kpts.get(RIGHT_EAR)) or midpoint(
            kpts.get(LEFT_EYE), kpts.get(RIGHT_EYE)
        )

        horiz = (nose[0] - neck[0]) / scale
        pitch_ratio = ((nose[1] - ear_mid[1]) / scale) if ear_mid else 0.0
        angle = pitch_ratio * 90.0

        if horiz <= -self._t.head_side_ratio:
            direction = "LEFT"
        elif horiz >= self._t.head_side_ratio:
            direction = "RIGHT"
        elif pitch_ratio >= self._t.head_down_ratio:
            direction = "DOWN"
        elif pitch_ratio <= self._t.head_up_ratio:
            direction = "UP"
        else:
            direction = "FORWARD"

        stability = self._stability(recent_angles)
        return HeadFeature(
            position=nose,
            angle=angle,
            direction=direction,
            stability=stability,
            available=True,
        )

    @staticmethod
    def _stability(recent_angles: Optional[List[float]]) -> float:
        """Độ ổn định 0..1 từ độ lệch chuẩn góc đầu gần đây."""
        if not recent_angles or len(recent_angles) < 2:
            return 1.0
        std = statistics.pstdev(recent_angles)
        return 1.0 / (1.0 + std / 10.0)
