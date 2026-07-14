"""
SittingFeatureExtractor — ước lượng ngồi/đứng từ hình học chân-thân.
"""

from __future__ import annotations

from typing import Tuple

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.models import Keypoints
from app.modules.behavior.models.keypoints import (
    LEFT_ANKLE,
    LEFT_HIP,
    LEFT_KNEE,
    LEFT_SHOULDER,
    RIGHT_ANKLE,
    RIGHT_HIP,
    RIGHT_KNEE,
    RIGHT_SHOULDER,
)
from app.modules.behavior.utils.geometry import distance, midpoint


class SittingFeatureExtractor:
    """Ước lượng tư thế ngồi/đứng."""

    def __init__(self, thresholds: ThresholdConfig) -> None:
        self._t = thresholds

    def extract(self, kpts: Keypoints) -> Tuple[str, bool]:
        """
        Ước lượng posture.

        Returns:
            (posture, sitting) — posture ∈ {SITTING, STANDING, UNKNOWN}.
        """
        neck = midpoint(kpts.get(LEFT_SHOULDER), kpts.get(RIGHT_SHOULDER))
        hip = midpoint(kpts.get(LEFT_HIP), kpts.get(RIGHT_HIP))
        if hip is None or neck is None:
            return ("UNKNOWN", False)

        torso = distance(neck, hip) or 1.0
        ankle = midpoint(kpts.get(LEFT_ANKLE), kpts.get(RIGHT_ANKLE))
        knee = midpoint(kpts.get(LEFT_KNEE), kpts.get(RIGHT_KNEE))

        # Chân bị che (thường ngồi sau bàn) → coi là ngồi
        if ankle is None or knee is None:
            return ("SITTING", True)

        leg_len = distance(hip, ankle) or 0.0
        ratio = leg_len / torso if torso else 0.0
        if ratio >= self._t.standing_leg_ratio:
            return ("STANDING", False)
        return ("SITTING", True)
