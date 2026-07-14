"""
TimelineManager — cập nhật timeline, lịch sử ROI (enter/leave/stay) & đường đi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from loguru import logger

from app.modules.tracking.models import ROI, Timeline
from app.modules.tracking.models.timeline import ROIVisit


@dataclass
class ROIEvent:
    """Sự kiện ROI để logging/phân tích."""

    kind: str  # "enter" | "leave"
    roi_id: str
    roi_name: str
    track_id: int


class TimelineManager:
    """Quản lý cập nhật timeline cho track (ROI transition, path)."""

    @staticmethod
    def update(
        timeline: Timeline,
        track_id: int,
        center: tuple[float, float],
        frame_id: int,
        timestamp: datetime,
        roi: Optional[ROI],
    ) -> List[ROIEvent]:
        """
        Cập nhật timeline theo frame mới.

        - Ghi last_seen/last_frame.
        - Thêm điểm path.
        - Xử lý ROI transition (enter/leave) + cập nhật stay_seconds.

        Args:
            timeline: Timeline của track.
            track_id: ID track (cho log).
            center: Tâm hiện tại.
            frame_id: Frame hiện tại.
            timestamp: Thời điểm.
            roi: ROI hiện tại (None nếu ngoài mọi ROI).

        Returns:
            Danh sách ROIEvent phát sinh (enter/leave).
        """
        timeline.last_seen = timestamp
        timeline.last_frame = frame_id
        timeline.add_point(center[0], center[1], frame_id)

        events: List[ROIEvent] = []
        open_visit = TimelineManager._open_visit(timeline)
        current_roi_id = open_visit.roi_id if open_visit else None
        new_roi_id = roi.id if roi else None

        if current_roi_id != new_roi_id:
            # Rời ROI cũ
            if open_visit is not None:
                open_visit.leave_time = timestamp
                open_visit.stay_seconds = (
                    open_visit.leave_time - open_visit.enter_time
                ).total_seconds()
                events.append(
                    ROIEvent("leave", open_visit.roi_id, open_visit.roi_name, track_id)
                )
                logger.debug(
                    "ROI leave | track={} roi={}", track_id, open_visit.roi_id
                )
            # Vào ROI mới
            if roi is not None:
                timeline.roi_history.append(
                    ROIVisit(
                        roi_id=roi.id,
                        roi_name=roi.name,
                        enter_time=timestamp,
                        enter_frame=frame_id,
                    )
                )
                events.append(ROIEvent("enter", roi.id, roi.name, track_id))
                logger.debug("ROI enter | track={} roi={}", track_id, roi.id)
        else:
            # Vẫn trong cùng ROI → cập nhật stay
            if open_visit is not None:
                open_visit.stay_seconds = (
                    timestamp - open_visit.enter_time
                ).total_seconds()

        return events

    @staticmethod
    def _open_visit(timeline: Timeline) -> Optional[ROIVisit]:
        """Lấy lần ghé ROI đang mở (chưa rời)."""
        if timeline.roi_history and timeline.roi_history[-1].leave_time is None:
            return timeline.roi_history[-1]
        return None

    @staticmethod
    def mark_lost(timeline: Timeline) -> None:
        """Tăng bộ đếm lost."""
        timeline.lost_count += 1

    @staticmethod
    def mark_recovered(timeline: Timeline) -> None:
        """Tăng bộ đếm recover."""
        timeline.recover_count += 1
