"""
MotionFeatureExtractor — đặc trưng chuyển động từ track + lịch sử.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from app.modules.behavior.models import MotionFeature
from app.modules.behavior.utils.geometry import distance

Point = Tuple[float, float]


class MotionFeatureExtractor:
    """Trích Stationary Time / Movement Distance / Speed / Direction."""

    def __init__(self, frame_rate: int, stationary_speed: float) -> None:
        self._frame_rate = max(1, frame_rate)
        self._stationary_speed = stationary_speed

    def extract(
        self,
        speed_px: float,
        direction: str,
        centers: List[Point],
        timestamps: List[datetime],
        speeds: List[float],
    ) -> MotionFeature:
        """
        Trích đặc trưng chuyển động.

        Args:
            speed_px: Tốc độ hiện tại (px/frame) từ Tracking Engine.
            direction: Hướng hiện tại từ Tracking Engine.
            centers: Lịch sử tâm (cũ→mới).
            timestamps: Lịch sử thời điểm (cũ→mới).
            speeds: Lịch sử tốc độ px/frame (cũ→mới).

        Returns:
            MotionFeature.
        """
        # Quãng đường di chuyển trong cửa sổ
        movement_distance = 0.0
        for i in range(1, len(centers)):
            d = distance(centers[i - 1], centers[i])
            if d:
                movement_distance += d

        # Thời gian đứng yên liên tục (tính từ cuối buffer trở về)
        stationary_time = 0.0
        if speeds and timestamps:
            end_idx = len(speeds) - 1
            i = end_idx
            while i >= 0 and speeds[i] < self._stationary_speed:
                i -= 1
            start_idx = i + 1
            if start_idx <= end_idx and start_idx < len(timestamps):
                stationary_time = (
                    timestamps[end_idx] - timestamps[start_idx]
                ).total_seconds()

        return MotionFeature(
            stationary_time=stationary_time,
            movement_distance=movement_distance,
            movement_speed=speed_px,
            direction=direction if speed_px >= self._stationary_speed else "STATIONARY",
        )
