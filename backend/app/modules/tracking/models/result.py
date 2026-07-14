"""
DTO — TrackingResult: đầu ra chuẩn của Tracking Engine cho một frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List

from app.modules.tracking.models.track import Track


@dataclass
class TrackingResult:
    """
    Kết quả tracking cho một frame — DTO chuẩn.

    Attributes:
        camera_id: Camera nguồn.
        frame_id: Số thứ tự frame.
        timestamp: Thời điểm frame.
        tracks: Danh sách Track đang hoạt động.
        processing_time_ms: Thời gian xử lý tracking (ms).
    """

    camera_id: int
    frame_id: int
    timestamp: datetime
    tracks: List[Track] = field(default_factory=list)
    processing_time_ms: float = 0.0

    @property
    def count(self) -> int:
        """Số track hoạt động."""
        return len(self.tracks)

    def to_dict(self) -> dict[str, Any]:
        """Serialize TrackingResult thành JSON DTO."""
        return {
            "camera_id": self.camera_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "tracks": [t.to_dict() for t in self.tracks],
            "count": self.count,
            "processing_time_ms": round(self.processing_time_ms, 2),
        }
