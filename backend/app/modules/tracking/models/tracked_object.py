"""
DTO — TrackedObject: đầu ra thô từ thuật toán tracking (trước khi enrich).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class TrackedObject:
    """
    Kết quả thô một track từ tracker (ByteTrack) cho một frame.

    Attributes:
        track_id: ID track ổn định do tracker gán.
        xyxy: Bounding box (x1,y1,x2,y2) pixel gốc.
        score: Confidence gắn với detection đã match.
        class_id: COCO class id (thường là person=0).
        class_name: Nhãn logic.
    """

    track_id: int
    xyxy: Tuple[float, float, float, float]
    score: float
    class_id: int = 0
    class_name: str = "person"
