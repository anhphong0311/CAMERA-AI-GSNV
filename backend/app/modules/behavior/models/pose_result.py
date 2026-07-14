"""
DTO — PoseResult: kết quả pose cho một người (bbox + keypoints).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from app.modules.behavior.models.keypoints import Keypoints


@dataclass
class PoseResult:
    """
    Kết quả pose estimation cho một người.

    Attributes:
        bbox: (x1, y1, x2, y2) khung người (pixel gốc).
        score: Confidence khung người.
        keypoints: Keypoints COCO-17.
    """

    bbox: Tuple[float, float, float, float]
    score: float
    keypoints: Keypoints

    def to_dict(self) -> dict[str, Any]:
        """Serialize pose result."""
        return {
            "bbox": [round(v, 1) for v in self.bbox],
            "score": round(self.score, 4),
            "keypoints": self.keypoints.to_list(),
        }
