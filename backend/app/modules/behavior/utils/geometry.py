"""
Geometry utils — hình học 2D cho trích xuất đặc trưng (thuần math).
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]


def distance(a: Optional[Point], b: Optional[Point]) -> Optional[float]:
    """Khoảng cách Euclid; None nếu thiếu điểm."""
    if a is None or b is None:
        return None
    return math.hypot(a[0] - b[0], a[1] - b[1])


def midpoint(a: Optional[Point], b: Optional[Point]) -> Optional[Point]:
    """Trung điểm; None nếu thiếu điểm."""
    if a is None or b is None:
        return None
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def angle_from_vertical(dx: float, dy: float) -> float:
    """
    Góc (độ) của vector (dx, dy) so với trục dọc hướng LÊN.

    Trục y ảnh hướng xuống. 0° = thẳng đứng lên; dương = lệch phải.
    """
    return math.degrees(math.atan2(dx, -dy))


def bbox_center(bbox: Tuple[float, float, float, float]) -> Point:
    """Tâm bbox."""
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def bbox_iou(
    a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]
) -> float:
    """IoU giữa 2 bbox xyxy."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def point_to_bbox_distance(
    point: Optional[Point], bbox: Tuple[float, float, float, float]
) -> Optional[float]:
    """Khoảng cách từ điểm tới tâm bbox."""
    if point is None:
        return None
    return distance(point, bbox_center(bbox))


def scale_from(
    left_shoulder: Optional[Point],
    right_shoulder: Optional[Point],
    bbox: Tuple[float, float, float, float],
) -> float:
    """
    Ước lượng thang đo cơ thể (px) để chuẩn hóa khoảng cách.

    Ưu tiên khoảng cách vai; fallback theo chiều cao bbox.
    """
    d = distance(left_shoulder, right_shoulder)
    if d and d > 1.0:
        return d
    return max(1.0, (bbox[3] - bbox[1]) * 0.35)
