"""
EventProcessor — pipeline xử lý một BehaviorEvent.

Receive → Validate → Save → EvidenceEngine (snapshot + video) → enqueue Notification.
KHÔNG gửi Telegram trực tiếp.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.modules.event.config import EventConfig
from app.modules.event.evidence.engine import EvidenceEngine
from app.modules.event.evidence.deferred import DeferredVideoJob
from app.modules.event.exceptions import InvalidEventError
from app.modules.event.queue.queues import BoundedQueue
from app.modules.event.repositories.store import EventStore
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import EventRecord
from app.modules.event.schemas.status import EventStatus


class EventProcessor:
    """Xử lý event tuần tự qua Evidence Engine + enqueue notification."""

    def __init__(
        self,
        config: EventConfig,
        store: EventStore,
        evidence_engine: EvidenceEngine,
        notification_queue: BoundedQueue[EventRecord],
    ) -> None:
        self._config = config
        self._store = store
        self._evidence = evidence_engine
        self._queue = notification_queue

    def process(self, event: BehaviorEventInput) -> EventRecord:
        """
        Chạy pipeline cho một event CONFIRMED.

        Raises:
            InvalidEventError: event không hợp lệ (validate bật).
        """
        if self._config.validate_events:
            event.validate()

        record = self._to_record(event)
        record.touch(EventStatus.VALIDATING)
        self._store.save(record)
        record.touch(EventStatus.PROCESSING)
        logger.info("Event Created event={} rule={}", record.event_id, record.rule_id)

        notify_ready = True

        if self._config.process_snapshot or self._config.process_video:
            try:
                snapshot, video, notify_ready, ready_at = self._evidence.capture(event)
                if snapshot:
                    record.snapshot = snapshot
                    if snapshot.status == "created":
                        record.touch(EventStatus.SNAPSHOT_CREATED)
                if video:
                    record.video = video
                    if video.status == "created":
                        record.touch(EventStatus.VIDEO_CREATED)
                    elif video.status == "pending":
                        record.touch(EventStatus.VIDEO_PENDING)
                # Video chưa sẵn → xếp hàng xuất sau; thông báo vẫn gửi ngay với snapshot
                if video is not None and getattr(video, "status", None) == "pending":
                    evidence_time = self._evidence.resolve_evidence_time(event)
                    self._evidence.deferred_queue.add(
                        DeferredVideoJob(
                            record=record,
                            evidence_time=evidence_time,
                            ready_at=ready_at,
                        )
                    )
                    notify_ready = True
            except Exception as exc:  # pragma: no cover
                logger.warning("Evidence bước lỗi event={}: {}", record.event_id, exc)
                record.error = f"evidence: {exc}"

        if record.metadata.get("evidence_time") is None and event.evidence_time:
            record.metadata["evidence_time"] = event.evidence_time.isoformat()

        self._store.save(record)

        if self._config.process_notification and notify_ready:
            self._queue.put(record)
        elif not notify_ready:
            logger.info(
                "Event {} chờ video post-roll trước khi gửi Telegram",
                record.event_id,
            )
        else:
            record.touch(EventStatus.COMPLETED)
            self._store.save(record)

        return record

    def complete_deferred(self, record: EventRecord) -> EventRecord:
        """Hoàn tất video deferred — không gửi lại Telegram (đã gửi lúc có snapshot)."""
        try:
            video, _ = self._evidence.process_deferred(record)
            if video:
                record.video = video
                if video.status == "created":
                    record.touch(EventStatus.VIDEO_CREATED)
        except Exception as exc:  # pragma: no cover
            logger.warning("Deferred video lỗi event={}: {}", record.event_id, exc)
            record.error = f"deferred_video: {exc}"
        if record.status not in (
            EventStatus.COMPLETED,
            EventStatus.NOTIFICATION_SENT,
            EventStatus.FAILED,
        ):
            record.touch(EventStatus.COMPLETED)
        self._store.save(record)
        return record

    def _to_record(self, event: BehaviorEventInput) -> EventRecord:
        meta = dict(event.metadata)
        if event.evidence_time:
            meta["evidence_time"] = event.evidence_time.isoformat()
        return EventRecord(
            event_id=event.event_id,
            camera_id=event.camera_id,
            camera_name=event.camera_name,
            track_id=event.track_id,
            rule_id=event.rule_id,
            event_type=event.event_type,
            severity=event.severity,
            confidence=event.confidence,
            start_time=event.start_time,
            end_time=event.end_time,
            duration=event.duration,
            roi=event.roi,
            status=EventStatus.NEW,
            metadata=meta,
        )
