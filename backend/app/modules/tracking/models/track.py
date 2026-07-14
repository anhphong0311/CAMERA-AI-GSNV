"""
DTO — Track: đối tượng track giàu thông tin (domain object, mutable).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Tuple

from app.modules.tracking.models.state import TrackState
from app.modules.tracking.models.timeline import Timeline


@dataclass
class Track:
    """
    Track giàu thông tin do TrackManager quản lý.

    Attributes:
        track_id: ID ổn định.
        camera_id: Camera nguồn.
        class_id / class_name: Loại đối tượng (person).
        bbox: (x1,y1,x2,y2) hiện tại.
        score: Confidence hiện tại.
        velocity: (vx, vy) px/frame.
        speed: Tốc độ chuẩn hóa (0-1 theo đường chéo khung hình).
        speed_px: Tốc độ px/frame.
        direction: Hướng di chuyển (LEFT/RIGHT/UP/DOWN/.../STATIONARY).
        current_roi_id / current_roi_name: ROI hiện tại.
        status: Trạng thái vòng đời.
        timeline: Timeline chi tiết.
        stationary_seconds: Thời gian đứng yên tích lũy.
    """

    track_id: int
    camera_id: int
    bbox: Tuple[float, float, float, float]
    score: float
    timeline: Timeline
    class_id: int = 0
    class_name: str = "person"
    velocity: Tuple[float, float] = (0.0, 0.0)
    speed: float = 0.0
    speed_px: float = 0.0
    direction: str = "STATIONARY"
    current_roi_id: Optional[str] = None
    current_roi_name: Optional[str] = None
    status: TrackState = TrackState.NEW
    stationary_seconds: float = 0.0

    @property
    def center(self) -> Tuple[float, float]:
        """Tâm bbox hiện tại."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @property
    def duration(self) -> float:
        """Thời gian xuất hiện (giây)."""
        return self.timeline.total_duration

    def to_dict(self) -> dict[str, Any]:
        """Serialize track theo DTO chuẩn TrackingResult."""
        cx, cy = self.center
        x1, y1, x2, y2 = self.bbox
        return {
            "track_id": self.track_id,
            "class": self.class_name,
            "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            "center": [round(cx, 1), round(cy, 1)],
            "velocity": [round(self.velocity[0], 2), round(self.velocity[1], 2)],
            "speed": round(self.speed, 4),
            "speed_px": round(self.speed_px, 2),
            "direction": self.direction,
            "roi": self.current_roi_name or self.current_roi_id,
            "duration": round(self.duration, 2),
            "status": self.status.value,
            "score": round(self.score, 4),
        }

    def to_detail_dict(self) -> dict[str, Any]:
        """Serialize đầy đủ (kèm timeline) cho endpoint chi tiết."""
        base = self.to_dict()
        base["timeline"] = self.timeline.to_dict()
        return base
