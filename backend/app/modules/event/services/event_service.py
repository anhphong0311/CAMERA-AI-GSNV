"""
EventService — facade Event Processing & Notification Center.

Kết nối: Ring Buffer ← frame; Event Queue → Event Processor → Snapshot/Video
→ Notification Queue → Telegram Worker (retry/dedup/cooldown). Cung cấp truy vấn
cho API và command cho Telegram Bot.

KHÔNG chứa logic AI/Tracking/Pose/Rule/Dashboard.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, List, Optional

import numpy as np
from loguru import logger

from app.modules.event.config import (
    EventConfig,
    NotificationConfig,
    RecorderConfig,
    SnapshotConfig,
    TelegramConfig,
    load_event_config,
    load_notification_config,
    load_recorder_config,
    load_snapshot_config,
    load_telegram_config,
)
from app.modules.event.event_processor import EventProcessor
from app.modules.event.evidence.config import load_evidence_config
from app.modules.event.evidence.engine import EvidenceEngine
from app.modules.event.evidence.frame_buffer import FrameBufferManager
from app.modules.event.exceptions import EventNotFoundError
from app.modules.event.history import notification_history, retry_history
from app.modules.event.notification import (
    NotificationProvider,
    NotificationWorker,
    ProviderRegistry,
    SendResult,
)
from app.modules.event.queue.queues import BoundedQueue
from app.modules.event.repositories.store import EventStore, InMemoryEventStore
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import EventRecord
from app.modules.event.snapshot import SnapshotService
from app.modules.event.telegram import BotContext, TelegramBot, TelegramProvider
from app.modules.event.video_recorder import VideoRecorder


class EventService:
    """Facade trung tâm xử lý event."""

    def __init__(
        self,
        event_config: Optional[EventConfig] = None,
        snapshot_config: Optional[SnapshotConfig] = None,
        recorder_config: Optional[RecorderConfig] = None,
        notification_config: Optional[NotificationConfig] = None,
        telegram_config: Optional[TelegramConfig] = None,
        store: Optional[EventStore] = None,
        provider: Optional[NotificationProvider] = None,
        sleeper=None,
    ) -> None:
        self._config = event_config or load_event_config()
        self._snapshot_config = snapshot_config or load_snapshot_config()
        self._recorder_config = recorder_config or load_recorder_config()
        self._notification_config = notification_config or load_notification_config()
        self._telegram_config = telegram_config or load_telegram_config()

        self._evidence_cfg = load_evidence_config()
        self._store = store or InMemoryEventStore(self._config.history_size)
        fb = self._evidence_cfg.frame_buffer
        self._buffers = FrameBufferManager(fb.seconds, fb.fps)
        self._snapshot = SnapshotService(self._snapshot_config)
        self._recorder = VideoRecorder(self._recorder_config)
        self._evidence = EvidenceEngine(
            self._buffers,
            self._snapshot_config,
            self._recorder_config,
            self._evidence_cfg,
        )

        self._event_queue: BoundedQueue[BehaviorEventInput] = BoundedQueue(
            self._notification_config.queue_max
        )
        self._notification_queue: BoundedQueue[EventRecord] = BoundedQueue(
            self._notification_config.queue_max
        )

        self._processor = EventProcessor(
            self._config,
            self._store,
            self._evidence,
            self._notification_queue,
        )
        self._system_control = None

        # Provider registry — Telegram mặc định, cho phép inject provider test
        self._registry = ProviderRegistry()
        self._telegram_provider = TelegramProvider(self._telegram_config)
        self._registry.register(self._telegram_provider)
        if provider is not None:
            self._registry.register(provider)

        self._worker = NotificationWorker(
            self._notification_queue,
            self._registry,
            self._store,
            self._notification_config,
            self._telegram_config.retry,
            sleeper=sleeper,
        )
        self._bot = TelegramBot(self._build_bot_context())

        self._lock = threading.RLock()
        self._running = False
        self._processed = 0

    # ----- frame ingestion (Ring Buffer) -----
    def push_frame(
        self,
        camera_id: int,
        frame: np.ndarray,
        timestamp: Optional[datetime] = None,
        frame_index: Optional[int] = None,
    ) -> None:
        """Đẩy frame camera vào evidence frame buffer."""
        self._buffers.push(camera_id, frame, timestamp, frame_index)

    # ----- event ingestion -----
    def ingest(self, event: BehaviorEventInput) -> None:
        """Nạp event vào Event Queue (không block)."""
        self._event_queue.put(event)

    def ingest_dict(self, data: dict[str, Any]) -> None:
        """Nạp event từ dict (vd BehaviorEventDTO.to_dict())."""
        self._event_queue.put(BehaviorEventInput.from_dict(data))

    def process_events(self) -> List[EventRecord]:
        """Xử lý toàn bộ event đang chờ trong Event Queue."""
        records: List[EventRecord] = []
        while True:
            event = self._event_queue.get()
            if event is None:
                break
            try:
                records.append(self._processor.process(event))
                self._processed += 1
            except Exception as exc:  # pragma: no cover
                logger.warning("Xử lý event lỗi: {}", exc)
        return records

    def drain_notifications(self) -> int:
        """Gửi toàn bộ notification đang chờ (Telegram Worker)."""
        return self._worker.drain()

    def run_once(self) -> List[EventRecord]:
        """Một chu kỳ: deferred video → process events → gửi notification."""
        records: List[EventRecord] = []
        for deferred in self._evidence.drain_deferred():
            existing = self._store.get(deferred.event_id)
            if existing:
                records.append(self._processor.complete_deferred(existing))
            else:
                records.append(self._processor.complete_deferred(deferred))
        records.extend(self.process_events())
        self.drain_notifications()
        return records

    def ingest_now(self, event: BehaviorEventInput) -> EventRecord:
        """Nạp + xử lý + gửi ngay một event (tiện cho test/đồng bộ)."""
        self.ingest(event)
        records = self.run_once()
        return records[-1] if records else self._store.get(event.event_id)

    # ----- retry / resend -----
    def retry(self, event_id: str) -> EventRecord:
        """Gửi lại notification cho event (áp dụng dedup/cooldown)."""
        record = self._require(event_id)
        self._worker.process(record, force=False)
        return record

    def resend(self, event_id: str, force: bool = True) -> EventRecord:
        """Gửi lại notification (force → bỏ qua dedup/cooldown)."""
        record = self._require(event_id)
        self._worker.process(record, force=force)
        return record

    # ----- queries -----
    def get_event(self, event_id: str) -> EventRecord:
        return self._require(event_id)

    def list_events(
        self, camera_id: Optional[int] = None, rule_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[EventRecord]:
        return self._store.list(camera_id=camera_id, rule_id=rule_id, limit=limit)

    def live_events(self) -> List[EventRecord]:
        return self._store.live()

    def event_history(
        self, camera_id: Optional[int] = None, limit: int = 200
    ) -> List[EventRecord]:
        return self._store.list(camera_id=camera_id, limit=limit)

    def notifications(self, limit: int = 200) -> List[dict[str, Any]]:
        return notification_history(self._store, limit)

    def retries(self, limit: int = 200) -> List[dict[str, Any]]:
        return retry_history(self._store, limit)

    def telegram_status(self) -> dict[str, Any]:
        """Trạng thái Telegram + queue."""
        return {
            "enabled": self._telegram_config.enabled,
            "ready": self._telegram_provider.is_ready,
            "channels": self._registry.names(),
            "ready_channels": self._registry.ready_names(),
            "notification_queue": self._notification_queue.size,
            "event_queue": self._event_queue.size,
        }

    def statistics(self) -> dict[str, Any]:
        """Thống kê tổng hợp."""
        return {
            "processed": self._processed,
            "store": self._store.statistics(),
            "ring_buffers": self._buffers.stats(),
            "deferred_video_jobs": self._evidence.deferred_queue.pending(),
            "telegram": self.telegram_status(),
        }

    def bind_system_control(self, control) -> None:
        """Gắn SystemControlService sau khi app khởi tạo xong."""
        self._system_control = control
        self._bot = TelegramBot(self._build_bot_context())

    def is_monitoring(self) -> bool:
        """True nếu hệ thống giám sát đang bật (mặc định True)."""
        if self._system_control is None:
            return True
        return bool(self._system_control.is_monitoring)

    async def handle_command(self, command: str) -> str:
        """Xử lý command Telegram bot (async vì /bat /tat)."""
        return await self._bot.handle(command)

    def send_telegram_text(self, chat_id: str, text: str) -> SendResult:
        """Gửi text trả lời lệnh bot."""
        return self._telegram_provider.send_text(chat_id, text)

    def send_test_notification(self) -> dict[str, Any]:
        """Gửi tin test PHONE_USAGE (format từ–đến) vào nhóm Telegram."""
        from datetime import datetime, timedelta, timezone

        from app.modules.event.notification.formatter import build_alert_message

        end = datetime.now(timezone.utc)
        start = end - timedelta(seconds=215)
        record = EventRecord(
            event_id="test-" + end.strftime("%Y%m%d%H%M%S"),
            camera_id=1,
            camera_name="CAM01",
            track_id=12,
            rule_id="PHONE_USAGE",
            event_type="PHONE_USAGE",
            severity="HIGH",
            confidence=0.96,
            start_time=start,
            end_time=end,
            duration=215.0,
            roi="Desk 01",
        )
        msg = build_alert_message(record)
        result = self._telegram_provider.send(msg)
        return {
            "ok": result.ok,
            "skipped": result.skipped,
            "target": result.target,
            "ready": self._telegram_provider.is_ready,
            "preview": msg.body,
        }

    # ----- helpers -----
    def _require(self, event_id: str) -> EventRecord:
        record = self._store.get(event_id)
        if record is None:
            raise EventNotFoundError(event_id)
        return record

    def _build_bot_context(self) -> BotContext:
        def status() -> str:
            st = self.telegram_status()
            return (
                f"AEMS Event Center\n"
                f"Telegram: {'sẵn sàng' if st['ready'] else 'tắt'}\n"
                f"Hàng đợi: {st['notification_queue']}\n"
                f"Đã xử lý: {self._processed}"
            )

        def cameras() -> List[str]:
            try:
                import httpx

                r = httpx.get(
                    "http://127.0.0.1:8000/api/v1/cameras", timeout=3.0
                )
                rows = r.json().get("data") or []
                return [
                    f"{c.get('name') or c.get('code')} (#{c.get('id')}) — {c.get('status')}"
                    for c in rows
                ]
            except Exception:
                ids = sorted({e.camera_id for e in self._store.list(limit=1000)})
                return [f"Camera {i}" for i in ids]

        def events(n: int) -> List[str]:
            return [
                f"{e.rule_id} track#{e.track_id} ({e.status.value})"
                for e in self._store.list(limit=n)
            ]

        def latest() -> str:
            items = self._store.list(limit=1)
            if not items:
                return "(chưa có event)"
            e = items[-1]
            return f"🚨 {e.rule_id} | Camera {e.camera_id} | Track #{e.track_id}"

        async def system_on() -> str:
            if self._system_control is None:
                return "Chưa gắn System Control."
            return await self._system_control.turn_on()

        async def system_off() -> str:
            if self._system_control is None:
                return "Chưa gắn System Control."
            return await self._system_control.turn_off()

        def system_status() -> str:
            if self._system_control is None:
                return "Chưa gắn System Control."
            return self._system_control.status_text()

        return BotContext(
            status_provider=status,
            cameras_provider=cameras,
            events_provider=events,
            latest_provider=latest,
            system_on=system_on if self._system_control else None,
            system_off=system_off if self._system_control else None,
            system_status=system_status if self._system_control else None,
        )

    def shutdown(self) -> None:
        """Dọn dẹp."""
        self._running = False
        self._event_queue.clear()
        self._notification_queue.clear()
        self._buffers.clear()
        logger.info("EventService shutdown.")
