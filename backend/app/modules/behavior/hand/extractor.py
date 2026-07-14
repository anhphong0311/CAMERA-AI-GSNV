"""
HandFeatureExtractor — trích đặc trưng tay (vị trí, chuyển động, gần mặt).
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.models import HandFeature, Keypoints
from app.modules.behavior.models.keypoints import (
    LEFT_SHOULDER,
    LEFT_WRIST,
    NOSE,
    RIGHT_SHOULDER,
    RIGHT_WRIST,
)
from app.modules.behavior.utils.geometry import distance, scale_from

Point = Tuple[float, float]


class HandFeatureExtractor:
    """Trích Hand Position/Movement/Speed/Near-Face."""

    def __init__(self, thresholds: ThresholdConfig) -> None:
        self._t = thresholds

    def extract(
        self,
        kpts: Keypoints,
        bbox: Tuple[float, float, float, float],
        prev_left: Optional[Point] = None,
        prev_right: Optional[Point] = None,
        dt_frames: float = 1.0,
    ) -> HandFeature:
        """
        Trích đặc trưng tay.

        Args:
            kpts: Keypoints.
            bbox: Khung người.
            prev_left/prev_right: Vị trí cổ tay frame trước (tính movement/speed).
            dt_frames: Số frame trôi qua.

        Returns:
            HandFeature.
        """
        lw = kpts.get(LEFT_WRIST)
        rw = kpts.get(RIGHT_WRIST)
        if lw is None and rw is None:
            return HandFeature(available=False)

        nose = kpts.get(NOSE)
        scale = scale_from(kpts.get(LEFT_SHOULDER), kpts.get(RIGHT_SHOULDER), bbox)

        # Gần mặt
        near_face = False
        for w in (lw, rw):
            d = distance(w, nose)
            if d is not None and d < self._t.hand_near_face_ratio * scale:
                near_face = True

        # Chuyển động / tốc độ
        movement = 0.0
        moves = []
        dl = distance(lw, prev_left)
        dr = distance(rw, prev_right)
        if dl is not None:
            moves.append(dl)
        if dr is not None:
            moves.append(dr)
        if moves:
            movement = max(moves)
        speed = movement / dt_frames if dt_frames > 0 else 0.0

        return HandFeature(
            left_position=lw,
            right_position=rw,
            movement=movement,
            speed=speed,
            near_face=near_face,
            available=True,
        )
