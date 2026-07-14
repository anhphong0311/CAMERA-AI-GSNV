"""
DTO — Keypoints (COCO 17) và tiện ích truy cập joint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

# Chỉ số keypoint COCO-17 (chuẩn YOLO Pose / MediaPipe map về)
NOSE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
LEFT_EAR = 3
RIGHT_EAR = 4
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16

KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]

# Cạnh skeleton để vẽ (cặp chỉ số keypoint)
SKELETON_EDGES = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15),
    (12, 14), (14, 16), (0, 5), (0, 6),
]

Point = Tuple[float, float]


@dataclass
class Keypoints:
    """
    Tập 17 keypoint COCO cho một người.

    Attributes:
        points: List[(x, y, confidence)] độ dài 17.
        min_conf: Ngưỡng confidence để coi joint hợp lệ.
    """

    points: List[Tuple[float, float, float]]
    min_conf: float = 0.3

    def get(self, index: int) -> Optional[Point]:
        """
        Lấy tọa độ (x, y) của joint nếu confidence đủ, ngược lại None.

        Args:
            index: Chỉ số keypoint COCO.

        Returns:
            (x, y) hoặc None nếu thiếu/không đủ tin cậy.
        """
        if index < 0 or index >= len(self.points):
            return None
        x, y, c = self.points[index]
        if c < self.min_conf:
            return None
        return (x, y)

    def confidence(self, index: int) -> float:
        """Confidence của một joint."""
        if 0 <= index < len(self.points):
            return self.points[index][2]
        return 0.0

    def valid_count(self) -> int:
        """Số joint hợp lệ."""
        return sum(1 for _, _, c in self.points if c >= self.min_conf)

    def to_list(self) -> List[List[float]]:
        """Serialize keypoints."""
        return [[round(x, 1), round(y, 1), round(c, 3)] for x, y, c in self.points]
