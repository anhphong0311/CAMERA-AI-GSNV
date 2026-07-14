"""
BehaviorFeatureEngine — orchestrator trích đặc trưng hành vi cho MỘT camera.

Nhận: TrackingResult + danh sách PoseResult (đã chạy pose) + detections (ngữ cảnh).
Trả: BehaviorResult (list BehaviorFeatureDTO).

KHÔNG chạy detection/tracking; KHÔNG rule/alert/telegram/db.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from loguru import logger

from app.modules.behavior.body import BodyFeatureExtractor
from app.modules.behavior.config import BehaviorConfig
from app.modules.behavior.exceptions import BehaviorException
from app.modules.behavior.feature_engine.associator import PoseAssociator
from app.modules.behavior.feature_engine.context import ObjectContext
from app.modules.behavior.feature_engine.interaction import InteractionExtractor
from app.modules.behavior.gaze import GazeFeatureExtractor
from app.modules.behavior.hand import HandFeatureExtractor
from app.modules.behavior.head import HeadFeatureExtractor
from app.modules.behavior.history import FrameSnapshot, HistoryManager
from app.modules.behavior.models import (
    BehaviorFeatureDTO,
    BehaviorResult,
    ChairFeature,
    HandFeature,
    HeadFeature,
    MotionFeature,
    PoseResult,
    TemporalFeature,
)
from app.modules.behavior.motion import MotionFeatureExtractor
from app.modules.behavior.sitting import SittingFeatureExtractor


class BehaviorFeatureEngine:
    """Trích đặc trưng hành vi cho một camera (giữ HistoryManager riêng)."""

    def __init__(self, camera_id: int, config: BehaviorConfig) -> None:
        self.camera_id = camera_id
        self._config = config
        t = config.thresholds
        self._associator = PoseAssociator(config.associator.iou_threshold)
        self._head = HeadFeatureExtractor(t)
        self._body = BodyFeatureExtractor(t)
        self._hand = HandFeatureExtractor(t)
        self._sitting = SittingFeatureExtractor(t)
        self._gaze = GazeFeatureExtractor()
        self._interaction = InteractionExtractor(t)
        self._motion = MotionFeatureExtractor(
            config.frame_rate, t.stationary_speed
        )
        self._history = HistoryManager(
            config.temporal.buffer_size, config.temporal.max_tracks
        )

    @property
    def history(self) -> HistoryManager:
        """History manager của camera."""
        return self._history

    def process(
        self,
        tracking_result,
        poses: List[PoseResult],
        detections: Optional[Sequence] = None,
    ) -> BehaviorResult:
        """
        Trích đặc trưng cho tất cả track trong frame.

        Args:
            tracking_result: TrackingResult (Sprint 4).
            poses: PoseResult của frame (từ PoseEstimator).
            detections: Detection objects (ngữ cảnh phone/cup/...); có thể None.

        Returns:
            BehaviorResult.
        """
        start = time.perf_counter()
        ctx = ObjectContext.from_detections(detections)
        monitor_present = ctx.has("monitor")
        assoc = self._associator.associate(tracking_result.tracks, poses)

        features: List[BehaviorFeatureDTO] = []
        for track in tracking_result.tracks:
            pose = assoc.get(track.track_id)
            try:
                dto = self._extract_track(
                    track,
                    pose,
                    ctx,
                    monitor_present,
                    tracking_result.frame_id,
                    tracking_result.timestamp,
                )
            except BehaviorException as exc:
                logger.warning(
                    "Feature extract lỗi cam={} track={}: {}",
                    self.camera_id,
                    track.track_id,
                    exc.message,
                )
                dto = self._minimal_dto(track, tracking_result.timestamp)
            features.append(dto)

        self._history.prune(tracking_result.frame_id)
        elapsed = (time.perf_counter() - start) * 1000.0
        logger.debug(
            "Behavior features cam={} frame={} tracks={} in {:.1f}ms",
            self.camera_id,
            tracking_result.frame_id,
            len(features),
            elapsed,
        )
        return BehaviorResult(
            camera_id=tracking_result.camera_id,
            frame_id=tracking_result.frame_id,
            timestamp=tracking_result.timestamp,
            features=features,
            processing_time_ms=elapsed,
        )

    def _extract_track(
        self,
        track,
        pose: Optional[PoseResult],
        ctx: ObjectContext,
        monitor_present: bool,
        frame_id: int,
        timestamp: datetime,
    ) -> BehaviorFeatureDTO:
        """Trích đặc trưng cho một track."""
        buf = self._history.get_or_create(track.track_id)
        dt_frames = max(1.0, float(frame_id - buf.last_frame_id)) if buf.size else 1.0
        prev_left, prev_right = buf.prev_wrists()
        prev_sitting = buf.prev_sitting()

        dto = BehaviorFeatureDTO(track_id=track.track_id, timestamp=timestamp)

        head = HeadFeature()
        hand = HandFeature()
        posture, sitting = "UNKNOWN", False
        phone_near = False
        head_angle: Optional[float] = None
        head_dir: Optional[str] = None
        left_wrist = right_wrist = None

        if pose is not None:
            kpts = pose.keypoints
            recent_angles = buf.head_angles(
                window=self._config.thresholds.head_stability_window
            )
            head = self._head.extract(kpts, pose.bbox, recent_angles)
            dto.head = head
            dto.body = self._body.extract(kpts, pose.bbox)
            hand = self._hand.extract(
                kpts, pose.bbox, prev_left, prev_right, dt_frames
            )
            posture, sitting = self._sitting.extract(kpts)

            phone_feature, phone_near = self._interaction.phone(
                kpts, ctx, person_bbox=track.bbox
            )
            hand.near_phone = phone_feature.near
            hand.distance_phone = phone_feature.distance_hand
            dto.hand = hand
            dto.food_feature = self._interaction.food(kpts, pose.bbox, ctx)

            chair = self._interaction.desk(
                kpts,
                pose.bbox,
                ctx,
                posture,
                sitting,
                body_in_roi=track.current_roi_id is not None,
            )
            if prev_sitting is True and sitting is False:
                chair.leaving_chair = True
            elif prev_sitting is False and sitting is True:
                chair.returning_chair = True
            dto.chair_feature = chair

            dto.gaze = self._gaze.extract(head, phone_near, monitor_present)

            # duration tay gần điện thoại (streak trước khi append)
            phone_feature.duration = (
                buf.phone_near_streak() + (1 if phone_near else 0)
            ) / max(1, self._config.frame_rate)
            dto.phone_feature = phone_feature

            head_angle = head.angle if head.available else None
            head_dir = head.direction if head.available else None
            left_wrist = hand.left_position
            right_wrist = hand.right_position
        else:
            # Không có pose → giữ đặc trưng ghế theo ROI, còn lại mặc định
            dto.chair_feature = ChairFeature(
                body_in_roi=track.current_roi_id is not None
            )

        # Cập nhật temporal buffer với snapshot frame hiện tại
        snapshot = FrameSnapshot(
            timestamp=timestamp,
            center=track.center,
            speed_px=track.speed_px,
            pose_present=pose is not None,
            head_angle=head_angle,
            head_direction=head_dir,
            left_wrist=left_wrist,
            right_wrist=right_wrist,
            sitting=sitting if pose is not None else None,
            phone_near=phone_near,
        )
        self._history.update(track.track_id, snapshot, frame_id)

        # Motion (dùng buffer đã gồm frame hiện tại)
        dto.motion = self._motion.extract(
            speed_px=track.speed_px,
            direction=track.direction,
            centers=buf.centers(window=self._config.temporal.window),
            timestamps=buf.timestamps(window=self._config.temporal.window),
            speeds=buf.speeds(window=self._config.temporal.window),
        )

        dto.temporal_feature = TemporalFeature(
            buffer_size=buf.capacity,
            pose_history=buf.pose_history_len(),
            motion_history=buf.size,
            head_history=buf.head_history_len(),
            hand_history=buf.hand_history_len(),
        )
        return dto

    def _minimal_dto(self, track, timestamp: datetime) -> BehaviorFeatureDTO:
        """DTO tối thiểu khi trích đặc trưng lỗi (chỉ motion)."""
        dto = BehaviorFeatureDTO(track_id=track.track_id, timestamp=timestamp)
        dto.motion = MotionFeature(
            movement_speed=track.speed_px, direction=track.direction
        )
        dto.chair_feature = ChairFeature(
            body_in_roi=track.current_roi_id is not None
        )
        return dto
