"""
EvidenceEngine — orchestrator độc lập cho snapshot + video evidence.

Không chụp ảnh tại thời điểm gửi Telegram.
Snapshot/video lấy từ frame buffer theo evidence_time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from loguru import logger

from app.modules.event.config import RecorderConfig, SnapshotConfig
from app.modules.event.evidence.config import EvidenceConfig, load_evidence_config
from app.modules.event.evidence.deferred import DeferredVideoQueue
from app.modules.event.evidence.frame_buffer import FrameBufferManager
from app.modules.event.evidence.snapshot_manager import SnapshotManager
from app.modules.event.evidence.video_manager import VideoEvidenceManager
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import EventRecord, SnapshotRecord, VideoRecord


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceEngine:
    """Engine bằng chứng — tách biệt khỏi Rule Engine và Telegram."""

    def __init__(
        self,
        frame_buffers: FrameBufferManager,
        snapshot_config: SnapshotConfig,
        recorder_config: RecorderConfig,
        evidence_config: Optional[EvidenceConfig] = None,
        deferred: Optional[DeferredVideoQueue] = None,
    ) -> None:
        self._buffers = frame_buffers
        self._cfg = evidence_config or load_evidence_config()
        self._snapshots = SnapshotManager(snapshot_config)
        self._videos = VideoEvidenceManager(recorder_config)
        self._deferred = deferred or DeferredVideoQueue()

    @property
    def deferred_queue(self) -> DeferredVideoQueue:
        return self._deferred

    def resolve_evidence_time(self, event: BehaviorEventInput) -> datetime:
        """Thời điểm evidence — phone: lúc đạt ngưỡng; leave: lúc xác nhận bàn trống."""
        if event.evidence_time is not None:
            return event.evidence_time
        meta = event.metadata or {}
        raw = meta.get("evidence_time")
        if raw:
            if isinstance(raw, datetime):
                return raw
            try:
                return datetime.fromisoformat(str(raw))
            except ValueError:
                pass
        if event.rule_id == "AWAY_FROM_DESK":
            # Ưu tiên thời điểm xác nhận (end_time) = ảnh bàn trống
            return event.end_time or event.start_time
        return event.start_time

    def capture(
        self, event: BehaviorEventInput
    ) -> Tuple[Optional[SnapshotRecord], Optional[VideoRecord], bool, datetime]:
        """
        Chụp snapshot + lên lịch/xuất video.

        Returns:
            (snapshot, video, notification_ready, ready_at)
        """
        buf = self._buffers.buffer(event.camera_id)
        evidence_time = self.resolve_evidence_time(event)
        event.evidence_time = evidence_time

        snapshot = self._snapshots.capture_at(event, buf, evidence_time)
        if snapshot and snapshot.status == "created":
            logger.info(
                "Evidence snapshot event={} at={}",
                event.event_id,
                evidence_time.isoformat(),
            )

        post = self._cfg.video.post_seconds
        ready_at = self._videos.ready_at(evidence_time, post)
        now = _now()
        if now >= ready_at:
            video = self._videos.export(event, buf, evidence_time)
            # Luôn sẵn sàng gửi Telegram ngay (snapshot đủ để cảnh báo)
            return snapshot, video, True, ready_at

        # Không chặn thông báo vì chờ video post-roll — gửi snapshot trước
        return (
            snapshot,
            VideoRecord(path="", status="pending"),
            True,
            ready_at,
        )

    def process_deferred(self, record: EventRecord) -> Tuple[Optional[VideoRecord], bool]:
        """Hoàn thành video deferred; trả (video, ready_for_notification)."""
        event = BehaviorEventInput(
            event_id=record.event_id,
            camera_id=record.camera_id,
            camera_name=record.camera_name,
            track_id=record.track_id,
            rule_id=record.rule_id,
            event_type=record.event_type,
            severity=record.severity,
            confidence=record.confidence,
            start_time=record.start_time,
            end_time=record.end_time,
            duration=record.duration,
            roi=record.roi,
            metadata=record.metadata,
            evidence_time=record.metadata.get("evidence_time")
            if record.metadata
            else None,
        )
        if isinstance(event.evidence_time, str):
            try:
                event.evidence_time = datetime.fromisoformat(event.evidence_time)
            except ValueError:
                event.evidence_time = record.start_time

        evidence_time = self.resolve_evidence_time(event)
        buf = self._buffers.buffer(record.camera_id)
        video = self._videos.export(event, buf, evidence_time)
        return video, True

    def drain_deferred(self) -> list[EventRecord]:
        """Xử lý các job video đã đủ post-roll."""
        completed: list[EventRecord] = []
        for job in self._deferred.ready():
            completed.append(job.record)
        return completed
