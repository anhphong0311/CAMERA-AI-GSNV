"""
DTO — Timeline: lịch sử vòng đời của một track.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, List, Optional, Tuple


@dataclass
class ROIVisit:
    """
    Một lần track ở trong một ROI.

    Attributes:
        roi_id: Mã ROI.
        roi_name: Tên ROI.
        enter_time: Thời điểm vào.
        enter_frame: Frame vào.
        leave_time: Thời điểm rời (None nếu còn ở trong).
        stay_seconds: Thời gian lưu lại (cập nhật liên tục).
    """

    roi_id: str
    roi_name: str
    enter_time: datetime
    enter_frame: int
    leave_time: Optional[datetime] = None
    stay_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize một lần ghé ROI."""
        return {
            "roi_id": self.roi_id,
            "roi_name": self.roi_name,
            "enter_time": self.enter_time.isoformat(),
            "enter_frame": self.enter_frame,
            "leave_time": self.leave_time.isoformat() if self.leave_time else None,
            "stay_seconds": round(self.stay_seconds, 2),
        }


@dataclass
class Timeline:
    """
    Timeline của một track — thời gian xuất hiện, lịch sử ROI & di chuyển.

    Attributes:
        first_seen / last_seen: Thời điểm xuất hiện đầu/cuối.
        first_frame / last_frame: Frame đầu/cuối.
        roi_history: Danh sách ROIVisit.
        movement_history: Đường đi (x, y, frame) — bounded.
        lost_count: Số lần mất.
        recover_count: Số lần phục hồi.
    """

    first_seen: datetime
    last_seen: datetime
    first_frame: int
    last_frame: int
    history_size: int = 60
    roi_history: List[ROIVisit] = field(default_factory=list)
    movement_history: Deque[Tuple[float, float, int]] = field(default_factory=deque)
    lost_count: int = 0
    recover_count: int = 0

    def __post_init__(self) -> None:
        # Giới hạn kích thước path để tránh tràn bộ nhớ
        if not isinstance(self.movement_history, deque):
            self.movement_history = deque(self.movement_history, maxlen=self.history_size)
        else:
            self.movement_history = deque(
                self.movement_history, maxlen=self.history_size
            )

    @property
    def total_duration(self) -> float:
        """Tổng thời gian xuất hiện (giây)."""
        return max(0.0, (self.last_seen - self.first_seen).total_seconds())

    def add_point(self, x: float, y: float, frame_id: int) -> None:
        """Thêm điểm vào movement_history."""
        self.movement_history.append((x, y, frame_id))

    def path(self) -> List[Tuple[float, float]]:
        """Trả đường đi dạng list điểm (x, y)."""
        return [(x, y) for x, y, _ in self.movement_history]

    def to_dict(self) -> dict[str, Any]:
        """Serialize timeline cho API."""
        return {
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "first_frame": self.first_frame,
            "last_frame": self.last_frame,
            "total_duration": round(self.total_duration, 2),
            "roi_history": [v.to_dict() for v in self.roi_history],
            "movement_history": [
                [round(x, 1), round(y, 1), f] for x, y, f in self.movement_history
            ],
            "lost_count": self.lost_count,
            "recover_count": self.recover_count,
        }
