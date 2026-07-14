"""
BodyFeatureExtractor — trích đặc trưng thân (angle, lean, rotation) — ước lượng.
"""

from __future__ import annotations

from typing import Tuple

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.models import BodyFeature, Keypoints
from app.modules.behavior.models.keypoints import (
    LEFT_HIP,
    LEFT_SHOULDER,
    RIGHT_HIP,
    RIGHT_SHOULDER,
)
from app.modules.behavior.utils.geometry import (
    angle_from_vertical,
    distance,
    midpoint,
    scale_from,
)


class BodyFeatureExtractor:
    """Trích Body Angle / Lean / Rotation."""

    def __init__(self, thresholds: ThresholdConfig) -> None:
        self._t = thresholds

    def extract(
        self, kpts: Keypoints, bbox: Tuple[float, float, float, float]
    ) -> BodyFeature:
        """Trích đặc trưng thân từ vai + hông."""
        ls = kpts.get(LEFT_SHOULDER)
        rs = kpts.get(RIGHT_SHOULDER)
        lh = kpts.get(LEFT_HIP)
        rh = kpts.get(RIGHT_HIP)
        neck = midpoint(ls, rs)
        hip_mid = midpoint(lh, rh)
        if neck is None or hip_mid is None:
            return BodyFeature(available=False)

        scale = scale_from(ls, rs, bbox)
        torso_len = distance(neck, hip_mid) or scale

        dx = neck[0] - hip_mid[0]
        dy = neck[1] - hip_mid[1]
        angle = angle_from_vertical(dx, dy)

        lean_ratio = dx / torso_len
        if lean_ratio >= self._t.lean_forward_ratio:
            lean = "FORWARD"
        elif lean_ratio <= -self._t.lean_forward_ratio:
            lean = "BACK"
        else:
            lean = "NEUTRAL"

        # Rotation ước lượng từ chênh lệch bề rộng vai và hông
        shoulder_w = distance(ls, rs) or scale
        hip_w = distance(lh, rh) or shoulder_w
        rotation = min(90.0, abs(shoulder_w - hip_w) / scale * 90.0)

        return BodyFeature(
            angle=angle, lean=lean, rotation=rotation, available=True
        )
