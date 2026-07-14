"""
TrackView — track tối giản (duck-typed) để nạp dữ liệu từ API / nguồn ngoài.

Cho phép Behavior Engine tiêu thụ mà không cần dựng đầy đủ Track (Timeline...)
của Tracking Engine. Ở pipeline thật, Behavior nhận trực tiếp Track thật.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class TrackView:
    """Track rút gọn phục vụ trích đặc trưng."""

    track_id: int
    camera_id: int
    bbox: Tuple[float, float, float, float]
    speed_px: float = 0.0
    direction: str = "STATIONARY"
    current_roi_id: Optional[str] = None

    @property
    def center(self) -> Tuple[float, float]:
        """Tâm bbox."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


@dataclass
class TrackingView:
    """TrackingResult rút gọn (duck-typed) cho Behavior Engine."""

    camera_id: int
    frame_id: int
    timestamp: datetime
    tracks: List[TrackView] = field(default_factory=list)
