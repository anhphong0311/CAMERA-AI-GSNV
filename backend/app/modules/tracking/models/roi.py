"""
DTO — ROI (Region of Interest) và kiểm tra point-in-polygon.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Tuple


@dataclass
class ROI:
    """
    Vùng quan tâm dạng đa giác.

    Attributes:
        id: Mã ROI (desk_01, door...).
        name: Tên hiển thị.
        polygon: Danh sách đỉnh [(x, y), ...] theo pixel khung hình.
        color: Màu hiển thị (hex).
        description: Mô tả.
    """

    id: str
    name: str
    polygon: List[Tuple[float, float]]
    color: str = "#3b82f6"
    description: str = ""

    def contains(self, x: float, y: float) -> bool:
        """
        Kiểm tra điểm (x, y) có nằm trong polygon không (ray casting).

        Args:
            x, y: Tọa độ điểm.

        Returns:
            bool: True nếu điểm nằm trong ROI.
        """
        poly = self.polygon
        n = len(poly)
        if n < 3:
            return False
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
            )
            if intersect:
                inside = not inside
            j = i
        return inside

    def to_dict(self) -> dict[str, Any]:
        """Serialize ROI cho API."""
        return {
            "id": self.id,
            "name": self.name,
            "polygon": [[round(px, 2), round(py, 2)] for px, py in self.polygon],
            "color": self.color,
            "description": self.description,
        }
