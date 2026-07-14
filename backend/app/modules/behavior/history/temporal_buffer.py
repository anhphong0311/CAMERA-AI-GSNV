"""
TemporalBuffer — buffer thời gian (mặc định 300 frame) cho một track.

Lưu Pose/Motion/Head/Hand history phục vụ đặc trưng thời gian.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, List, Optional, Tuple

Point = Tuple[float, float]


@dataclass
class FrameSnapshot:
    """Snapshot đặc trưng của một frame cho một track."""

    timestamp: datetime
    center: Point
    speed_px: float
    pose_present: bool
    head_angle: Optional[float]
    head_direction: Optional[str]
    left_wrist: Optional[Point]
    right_wrist: Optional[Point]
    sitting: Optional[bool]
    phone_near: bool


class TemporalBuffer:
    """Ring buffer bounded các FrameSnapshot cho một track."""

    def __init__(self, buffer_size: int = 300) -> None:
        self._buffer_size = buffer_size
        self._items: Deque[FrameSnapshot] = deque(maxlen=buffer_size)
        self.last_frame_id: int = -1

    @property
    def size(self) -> int:
        """Số snapshot đang lưu."""
        return len(self._items)

    @property
    def capacity(self) -> int:
        """Sức chứa buffer."""
        return self._buffer_size

    def append(self, snapshot: FrameSnapshot, frame_id: int) -> None:
        """Thêm snapshot (tự drop cũ nhất khi đầy)."""
        self._items.append(snapshot)
        self.last_frame_id = frame_id

    def latest(self) -> Optional[FrameSnapshot]:
        """Snapshot mới nhất."""
        return self._items[-1] if self._items else None

    def centers(self, window: Optional[int] = None) -> List[Point]:
        """Lịch sử tâm (cũ→mới)."""
        items = self._tail(window)
        return [s.center for s in items]

    def timestamps(self, window: Optional[int] = None) -> List[datetime]:
        """Lịch sử thời điểm (cũ→mới)."""
        items = self._tail(window)
        return [s.timestamp for s in items]

    def speeds(self, window: Optional[int] = None) -> List[float]:
        """Lịch sử tốc độ px/frame (cũ→mới)."""
        items = self._tail(window)
        return [s.speed_px for s in items]

    def head_angles(self, window: Optional[int] = None) -> List[float]:
        """Lịch sử góc đầu hợp lệ (cũ→mới)."""
        items = self._tail(window)
        return [s.head_angle for s in items if s.head_angle is not None]

    def prev_wrists(self) -> Tuple[Optional[Point], Optional[Point]]:
        """Cổ tay của snapshot ngay trước (để tính movement)."""
        if len(self._items) < 1:
            return (None, None)
        prev = self._items[-1]
        return (prev.left_wrist, prev.right_wrist)

    def phone_near_streak(self) -> int:
        """Số frame liên tục gần đây tay gần điện thoại."""
        count = 0
        for s in reversed(self._items):
            if s.phone_near:
                count += 1
            else:
                break
        return count

    def prev_sitting(self) -> Optional[bool]:
        """Trạng thái ngồi snapshot trước."""
        if not self._items:
            return None
        return self._items[-1].sitting

    def pose_history_len(self) -> int:
        """Số frame có pose hợp lệ."""
        return sum(1 for s in self._items if s.pose_present)

    def hand_history_len(self) -> int:
        """Số frame có ít nhất một cổ tay."""
        return sum(
            1 for s in self._items if s.left_wrist or s.right_wrist
        )

    def head_history_len(self) -> int:
        """Số frame có góc đầu."""
        return sum(1 for s in self._items if s.head_angle is not None)

    def _tail(self, window: Optional[int]) -> List[FrameSnapshot]:
        items = list(self._items)
        if window is not None and window < len(items):
            return items[-window:]
        return items
