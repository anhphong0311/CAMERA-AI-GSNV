"""
Domain DTO — kết quả detection (in-memory, không phải ORM).

DetectionResult là DTO chuẩn để các module khác (Sprint 4+) tiêu thụ.
Detection Engine chỉ trả về cấu trúc này, không biết gì về DB/tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Tuple


def utc_now() -> datetime:
    """Trả về datetime UTC hiện tại."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BoundingBox:
    """
    Hộp giới hạn theo pixel gốc của frame (x1,y1 top-left; x2,y2 bottom-right).

    Frozen (immutable) để an toàn khi truyền giữa thread/module.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        """Chiều rộng box."""
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        """Chiều cao box."""
        return max(0.0, self.y2 - self.y1)

    @property
    def center(self) -> Tuple[float, float]:
        """Tọa độ tâm (cx, cy)."""
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    @property
    def area(self) -> float:
        """Diện tích box."""
        return self.width * self.height

    def to_xyxy(self) -> Tuple[float, float, float, float]:
        """Trả tuple (x1,y1,x2,y2)."""
        return (self.x1, self.y1, self.x2, self.y2)

    def to_dict(self) -> dict[str, float]:
        """Serialize bbox cho JSON."""
        return {
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
        }


@dataclass(frozen=True)
class Detection:
    """
    Một object được phát hiện.

    Attributes:
        class_name: Nhãn logic (person, phone, cup, ...).
        confidence: Độ tin cậy 0-1.
        bbox: Bounding box pixel gốc.
        class_id: COCO class id gốc (tham chiếu).
    """

    class_name: str
    confidence: float
    bbox: BoundingBox
    class_id: int = -1

    def to_dict(self) -> dict[str, Any]:
        """Serialize detection theo DTO chuẩn (class/confidence/bbox/center/w/h)."""
        cx, cy = self.bbox.center
        return {
            "class": self.class_name,
            "class_id": self.class_id,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox.to_dict(),
            "center": {"x": round(cx, 2), "y": round(cy, 2)},
            "width": round(self.bbox.width, 2),
            "height": round(self.bbox.height, 2),
        }


@dataclass
class DetectionResult:
    """
    Kết quả detection cho một frame — DTO chuẩn đầu ra Detection Engine.

    Attributes:
        camera_id: ID camera nguồn (do caller cung cấp, engine không tra DB).
        frame_id: Số thứ tự frame.
        timestamp: Thời điểm frame (UTC).
        objects: Danh sách Detection.
        inference_time_ms: Thời gian inference (ms).
        model_name: Tên model đã dùng.
        width/height: Kích thước frame gốc.
    """

    camera_id: int
    frame_id: int
    timestamp: datetime
    objects: List[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    model_name: str = "unknown"
    width: int = 0
    height: int = 0

    @property
    def fps(self) -> float:
        """FPS tức thời suy ra từ inference_time_ms."""
        if self.inference_time_ms <= 0:
            return 0.0
        return 1000.0 / self.inference_time_ms

    @property
    def count(self) -> int:
        """Số object phát hiện."""
        return len(self.objects)

    def to_dict(self) -> dict[str, Any]:
        """Serialize toàn bộ result thành JSON DTO."""
        return {
            "camera_id": self.camera_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "objects": [o.to_dict() for o in self.objects],
            "count": self.count,
            "inference_time_ms": round(self.inference_time_ms, 2),
            "model_name": self.model_name,
            "fps": round(self.fps, 2),
            "width": self.width,
            "height": self.height,
        }
