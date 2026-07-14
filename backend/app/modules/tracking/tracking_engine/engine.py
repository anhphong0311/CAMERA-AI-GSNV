"""
TrackingEngine — orchestrator tracking cho MỘT camera.

DetectionResult → (lọc person) → Tracker → TrackManager → TrackingResult.
Độc lập từng camera: không chia sẻ track id, không đọc camera, không AI.
"""

from __future__ import annotations

import math
import time
from typing import List, Optional

from loguru import logger

from app.modules.ai.models import DetectionResult
from app.modules.tracking.config import ROIRegionConfig, TrackingConfig
from app.modules.tracking.exceptions import InvalidDetectionError
from app.modules.tracking.models import Track, TrackingResult
from app.modules.tracking.roi.roi_manager import ROIManager
from app.modules.tracking.timeline.motion import MotionAnalyzer
from app.modules.tracking.track_manager.manager import TrackManager
from app.modules.tracking.tracking_engine.base_tracker import DetectionInput
from app.modules.tracking.tracking_engine.factory import create_tracker

# Chỉ theo dõi người trong Sprint 4
_TRACK_CLASS = "person"


class TrackingEngine:
    """Engine tracking độc lập cho một camera."""

    def __init__(
        self,
        camera_id: int,
        config: TrackingConfig,
        roi_configs: Optional[List[ROIRegionConfig]] = None,
    ) -> None:
        self.camera_id = camera_id
        self._config = config
        self._tracker = create_tracker(config.tracker)
        self._roi_manager = ROIManager.from_config(roi_configs or [])
        self._motion = MotionAnalyzer(config.motion.stationary_speed, 1000.0)
        self._track_manager = TrackManager(
            camera_id=camera_id,
            lifecycle=config.lifecycle,
            roi_manager=self._roi_manager,
            motion_analyzer=self._motion,
            history_size=config.motion.history_size,
        )
        self._frame_size_set = False
        self._last_result: Optional[TrackingResult] = None

    def update(self, detection: DetectionResult) -> TrackingResult:
        """
        Cập nhật tracking từ một DetectionResult.

        Args:
            detection: DetectionResult từ Detection Engine (Sprint 3).

        Returns:
            TrackingResult DTO.

        Raises:
            InvalidDetectionError: DetectionResult None.
        """
        if detection is None:
            raise InvalidDetectionError("DetectionResult là None.")

        start = time.perf_counter()

        if not self._frame_size_set and detection.width and detection.height:
            self._motion.set_frame_size(detection.width, detection.height)
            self._frame_size_set = True

        # Lọc chỉ person (Sprint 4 chỉ theo dõi người)
        inputs: List[DetectionInput] = []
        for obj in detection.objects:
            if obj.class_name != _TRACK_CLASS:
                continue
            inputs.append(
                DetectionInput(
                    xyxy=obj.bbox.to_xyxy(),
                    score=obj.confidence,
                    class_id=obj.class_id,
                    class_name=obj.class_name,
                )
            )

        tracked_objects = self._tracker.update(inputs)
        active = self._track_manager.update(
            tracked_objects, detection.frame_id, detection.timestamp
        )

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        result = TrackingResult(
            camera_id=self.camera_id,
            frame_id=detection.frame_id,
            timestamp=detection.timestamp,
            tracks=active,
            processing_time_ms=elapsed_ms,
        )
        self._last_result = result
        return result

    # ----- Truy vấn -----
    def get_last_result(self) -> Optional[TrackingResult]:
        """TrackingResult gần nhất."""
        return self._last_result

    def get_active_tracks(self) -> List[Track]:
        """Track đang hoạt động."""
        return self._track_manager.get_active_tracks()

    def get_track(self, track_id: int) -> Optional[Track]:
        """Lấy track theo id."""
        return self._track_manager.get_track(track_id)

    def get_history(self) -> List[Track]:
        """Track đã kết thúc."""
        return self._track_manager.get_history()

    def statistics(self) -> dict:
        """Thống kê tracking + ROI của camera."""
        stats = self._track_manager.statistics()
        stats["tracker"] = self._tracker.name
        stats["roi_count"] = len(self._roi_manager.regions)
        return stats

    @property
    def roi_manager(self) -> ROIManager:
        """ROIManager của camera."""
        return self._roi_manager

    def reset(self) -> None:
        """Reset tracker (dùng khi cần)."""
        self._tracker.reset()
