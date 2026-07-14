"""
MotionAnalyzer — tính vận tốc, tốc độ, hướng, quãng đường.

Thuần hình học 2D — không AI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class MotionState:
    """Kết quả phân tích chuyển động một bước."""

    velocity: Tuple[float, float]
    speed_px: float
    speed_norm: float
    direction: str
    distance: float


def compute_direction(vx: float, vy: float, stationary_speed: float) -> str:
    """
    Suy hướng di chuyển 8 phương từ vector vận tốc.

    Lưu ý: trục y ảnh hướng xuống → vy>0 nghĩa là đi XUỐNG (DOWN).

    Args:
        vx, vy: Thành phần vận tốc (px/frame).
        stationary_speed: Ngưỡng đứng yên.

    Returns:
        str: LEFT/RIGHT/UP/DOWN/UP-LEFT/... hoặc STATIONARY.
    """
    speed = math.hypot(vx, vy)
    if speed < stationary_speed:
        return "STATIONARY"
    angle = math.degrees(math.atan2(vy, vx))  # -180..180, 0 = phải, 90 = xuống
    # Chia 8 hướng
    dirs = [
        (-22.5, 22.5, "RIGHT"),
        (22.5, 67.5, "DOWN-RIGHT"),
        (67.5, 112.5, "DOWN"),
        (112.5, 157.5, "DOWN-LEFT"),
        (157.5, 180.01, "LEFT"),
        (-180.01, -157.5, "LEFT"),
        (-157.5, -112.5, "UP-LEFT"),
        (-112.5, -67.5, "UP"),
        (-67.5, -22.5, "UP-RIGHT"),
    ]
    for lo, hi, name in dirs:
        if lo <= angle < hi:
            return name
    return "STATIONARY"


class MotionAnalyzer:
    """Phân tích chuyển động dựa trên center hiện tại và trước đó."""

    def __init__(self, stationary_speed: float, frame_diagonal: float) -> None:
        self._stationary_speed = stationary_speed
        self._frame_diagonal = max(1.0, frame_diagonal)

    def set_frame_size(self, width: float, height: float) -> None:
        """Cập nhật đường chéo khung hình để chuẩn hóa tốc độ."""
        self._frame_diagonal = max(1.0, math.hypot(width, height))

    def analyze(
        self,
        prev_center: Tuple[float, float] | None,
        curr_center: Tuple[float, float],
        dt_frames: float = 1.0,
    ) -> MotionState:
        """
        Tính vận tốc/tốc độ/hướng/khoảng cách giữa 2 frame.

        Args:
            prev_center: Tâm frame trước (None nếu track mới).
            curr_center: Tâm frame hiện tại.
            dt_frames: Số frame trôi qua (>=1).

        Returns:
            MotionState.
        """
        if prev_center is None or dt_frames <= 0:
            return MotionState((0.0, 0.0), 0.0, 0.0, "STATIONARY", 0.0)

        dx = curr_center[0] - prev_center[0]
        dy = curr_center[1] - prev_center[1]
        vx = dx / dt_frames
        vy = dy / dt_frames
        speed_px = math.hypot(vx, vy)
        speed_norm = speed_px / self._frame_diagonal
        distance = math.hypot(dx, dy)
        direction = compute_direction(vx, vy, self._stationary_speed)
        return MotionState((vx, vy), speed_px, speed_norm, direction, distance)
