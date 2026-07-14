"""
ObjectContext — ngữ cảnh vật thể (phone/cup/bottle/food/monitor/chair) quanh người.

Nhận danh sách detection (duck-typed: có .class_name và .bbox) hoặc (name, xyxy)
để tính khoảng cách tay↔điện thoại, đồ ăn↔miệng... KHÔNG chạy detection ở đây.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List, Optional, Sequence, Tuple

from app.modules.behavior.utils.geometry import bbox_center, distance

BBox = Tuple[float, float, float, float]
Point = Tuple[float, float]


class ObjectContext:
    """Tra cứu vật thể theo lớp + khoảng cách gần nhất tới một điểm."""

    def __init__(self, objects: Iterable[Tuple[str, BBox]]) -> None:
        self._by_class: dict[str, List[BBox]] = defaultdict(list)
        for name, box in objects:
            self._by_class[name.lower()].append(tuple(box))  # type: ignore[arg-type]

    @classmethod
    def from_detections(cls, detections: Optional[Sequence]) -> "ObjectContext":
        """
        Tạo từ danh sách Detection (duck-typed) hoặc rỗng.

        Mỗi phần tử cần có .class_name và .bbox (có .to_xyxy() hoặc tuple).
        """
        items: List[Tuple[str, BBox]] = []
        for d in detections or []:
            bbox = getattr(d, "bbox", None)
            if bbox is None:
                continue
            if hasattr(bbox, "to_xyxy"):
                box = bbox.to_xyxy()
            else:
                box = tuple(bbox)
            items.append((getattr(d, "class_name", "unknown"), box))
        return cls(items)

    def boxes(self, class_name: str) -> List[BBox]:
        """Danh sách bbox của một lớp."""
        return self._by_class.get(class_name.lower(), [])

    def has(self, class_name: str) -> bool:
        """Có xuất hiện lớp không."""
        return bool(self.boxes(class_name))

    def nearest_distance(
        self, class_name: str, point: Optional[Point]
    ) -> Optional[float]:
        """Khoảng cách nhỏ nhất từ point tới tâm bbox của lớp; None nếu thiếu."""
        if point is None:
            return None
        best: Optional[float] = None
        for box in self.boxes(class_name):
            d = distance(point, bbox_center(box))
            if d is not None and (best is None or d < best):
                best = d
        return best

    def nearest_box(self, class_name: str, point: Optional[Point]) -> Optional[BBox]:
        """Bbox gần point nhất của lớp."""
        if point is None:
            return None
        best_box: Optional[BBox] = None
        best_d: Optional[float] = None
        for box in self.boxes(class_name):
            d = distance(point, bbox_center(box))
            if d is not None and (best_d is None or d < best_d):
                best_d = d
                best_box = box
        return best_box
