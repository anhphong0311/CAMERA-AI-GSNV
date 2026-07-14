"""
TrackManager — quản lý vòng đời Track giàu thông tin cho MỘT camera.

Nhận TrackedObject (thô từ tracker) → tạo/cập nhật Track domain:
state machine (NEW/TRACKING/LOST/RECOVERED/REMOVED), motion, ROI, timeline, history.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional, Sequence

from loguru import logger

from app.modules.tracking.config import LifecycleConfig
from app.modules.tracking.models import (
    ROI,
    Timeline,
    Track,
    TrackedObject,
    TrackState,
)
from app.modules.tracking.roi.roi_manager import ROIManager
from app.modules.tracking.timeline.motion import MotionAnalyzer
from app.modules.tracking.timeline.timeline_manager import TimelineManager


class TrackManager:
    """Quản lý tập Track cho một camera (create/update/lost/recover/remove)."""

    def __init__(
        self,
        camera_id: int,
        lifecycle: LifecycleConfig,
        roi_manager: ROIManager,
        motion_analyzer: MotionAnalyzer,
        history_size: int,
    ) -> None:
        self._camera_id = camera_id
        self._lifecycle = lifecycle
        self._roi = roi_manager
        self._motion = motion_analyzer
        self._history_size = history_size
        self._tracks: Dict[int, Track] = {}
        self._history: Deque[Track] = deque(maxlen=500)
        # Thống kê
        self._total_created = 0
        self._total_removed = 0
        self._total_lost = 0
        self._total_recovered = 0

    # ----- Cập nhật một frame -----
    def update(
        self,
        tracked_objects: Sequence[TrackedObject],
        frame_id: int,
        timestamp: datetime,
    ) -> List[Track]:
        """
        Cập nhật toàn bộ track theo output tracker của một frame.

        Returns:
            Danh sách Track đang hoạt động (NEW/TRACKING/RECOVERED).
        """
        active_ids = set()
        for obj in tracked_objects:
            active_ids.add(obj.track_id)
            if obj.track_id in self._tracks:
                self._update_existing(self._tracks[obj.track_id], obj, frame_id, timestamp)
            else:
                self._create_track(obj, frame_id, timestamp)

        # Track không xuất hiện frame này → LOST / REMOVED
        self._handle_missing(active_ids, frame_id)

        # Chống tràn track
        self._enforce_capacity()

        return [
            t
            for t in self._tracks.values()
            if t.status in (TrackState.NEW, TrackState.TRACKING, TrackState.RECOVERED)
        ]

    def _create_track(
        self, obj: TrackedObject, frame_id: int, timestamp: datetime
    ) -> None:
        """Tạo track mới (NEW)."""
        cx = (obj.xyxy[0] + obj.xyxy[2]) / 2.0
        cy = (obj.xyxy[1] + obj.xyxy[3]) / 2.0
        timeline = Timeline(
            first_seen=timestamp,
            last_seen=timestamp,
            first_frame=frame_id,
            last_frame=frame_id,
            history_size=self._history_size,
        )
        roi = self._roi.locate(cx, cy)
        track = Track(
            track_id=obj.track_id,
            camera_id=self._camera_id,
            bbox=obj.xyxy,
            score=obj.score,
            timeline=timeline,
            class_id=obj.class_id,
            class_name=obj.class_name,
            status=TrackState.NEW,
        )
        TimelineManager.update(timeline, obj.track_id, (cx, cy), frame_id, timestamp, roi)
        track.current_roi_id = roi.id if roi else None
        track.current_roi_name = roi.name if roi else None
        self._tracks[obj.track_id] = track
        self._total_created += 1
        logger.info(
            "Track created | camera={} track={} roi={}",
            self._camera_id,
            obj.track_id,
            track.current_roi_id,
        )

    def _update_existing(
        self, track: Track, obj: TrackedObject, frame_id: int, timestamp: datetime
    ) -> None:
        """Cập nhật track đã tồn tại (TRACKING hoặc RECOVERED nếu vừa LOST)."""
        was_lost = track.status == TrackState.LOST
        prev_point = (
            track.timeline.movement_history[-1]
            if track.timeline.movement_history
            else None
        )
        prev_center = (prev_point[0], prev_point[1]) if prev_point else None
        prev_frame = prev_point[2] if prev_point else frame_id
        dt = max(1, frame_id - prev_frame)

        cx = (obj.xyxy[0] + obj.xyxy[2]) / 2.0
        cy = (obj.xyxy[1] + obj.xyxy[3]) / 2.0
        motion = self._motion.analyze(prev_center, (cx, cy), dt)

        track.bbox = obj.xyxy
        track.score = obj.score
        track.velocity = motion.velocity
        track.speed = motion.speed_norm
        track.speed_px = motion.speed_px
        track.direction = motion.direction
        if motion.direction == "STATIONARY":
            track.stationary_seconds += 0.0  # cập nhật ở engine theo dt thực nếu cần

        roi = self._roi.locate(cx, cy)
        TimelineManager.update(
            track.timeline, track.track_id, (cx, cy), frame_id, timestamp, roi
        )
        track.current_roi_id = roi.id if roi else None
        track.current_roi_name = roi.name if roi else None

        if was_lost:
            track.status = TrackState.RECOVERED
            TimelineManager.mark_recovered(track.timeline)
            self._total_recovered += 1
            logger.info(
                "Track recovered | camera={} track={}",
                self._camera_id,
                track.track_id,
            )
        else:
            track.status = TrackState.TRACKING

    def _handle_missing(self, active_ids: set[int], frame_id: int) -> None:
        """Xử lý track không xuất hiện frame này → LOST → REMOVED."""
        to_remove: List[int] = []
        for track_id, track in self._tracks.items():
            if track_id in active_ids:
                continue
            if track.status != TrackState.LOST:
                track.status = TrackState.LOST
                TimelineManager.mark_lost(track.timeline)
                self._total_lost += 1
                logger.info(
                    "Track lost | camera={} track={}", self._camera_id, track_id
                )
            # Quá hạn → REMOVED
            if frame_id - track.timeline.last_frame > self._lifecycle.max_lost_frames:
                track.status = TrackState.REMOVED
                to_remove.append(track_id)

        for track_id in to_remove:
            removed = self._tracks.pop(track_id)
            self._history.append(removed)
            self._total_removed += 1
            logger.info("Track removed | camera={} track={}", self._camera_id, track_id)

    def _enforce_capacity(self) -> None:
        """Chống tràn: nếu vượt max_tracks, loại các track LOST cũ nhất."""
        max_tracks = self._lifecycle.max_tracks
        if len(self._tracks) <= max_tracks:
            return
        lost = sorted(
            (t for t in self._tracks.values() if t.status == TrackState.LOST),
            key=lambda t: t.timeline.last_frame,
        )
        for track in lost:
            if len(self._tracks) <= max_tracks:
                break
            self._tracks.pop(track.track_id, None)
            self._history.append(track)
            logger.warning(
                "Track evicted (capacity) | camera={} track={}",
                self._camera_id,
                track.track_id,
            )

    # ----- Truy vấn -----
    def get_active_tracks(self) -> List[Track]:
        """Track đang hoạt động (không LOST/REMOVED)."""
        return [
            t
            for t in self._tracks.values()
            if t.status in (TrackState.NEW, TrackState.TRACKING, TrackState.RECOVERED)
        ]

    def get_all_tracks(self) -> List[Track]:
        """Toàn bộ track còn trong bộ nhớ (kể cả LOST)."""
        return list(self._tracks.values())

    def get_track(self, track_id: int) -> Optional[Track]:
        """Lấy track theo id (ưu tiên đang sống, sau đó history)."""
        if track_id in self._tracks:
            return self._tracks[track_id]
        for t in self._history:
            if t.track_id == track_id:
                return t
        return None

    def get_history(self) -> List[Track]:
        """Track đã REMOVED (history bounded)."""
        return list(self._history)

    def statistics(self) -> dict:
        """Thống kê tracking của camera."""
        active = self.get_active_tracks()
        lost = [t for t in self._tracks.values() if t.status == TrackState.LOST]
        return {
            "camera_id": self._camera_id,
            "active_tracks": len(active),
            "lost_tracks": len(lost),
            "total_created": self._total_created,
            "total_removed": self._total_removed,
            "total_lost": self._total_lost,
            "total_recovered": self._total_recovered,
            "in_memory": len(self._tracks),
            "history": len(self._history),
        }
