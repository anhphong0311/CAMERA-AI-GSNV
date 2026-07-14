"""
NotificationWorker — tiêu thụ Notification Queue, gửi qua provider (retry/dedup).

Behavior Event → Notification Queue → Worker → Telegram (không gửi trực tiếp).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.modules.event.config import NotificationConfig, RetryConfig
from app.modules.event.notification.dedup import DedupCooldown
from app.modules.event.notification.formatter import build_alert_message
from app.modules.event.notification.registry import ProviderRegistry
from app.modules.event.queue.queues import BoundedQueue
from app.modules.event.repositories.store import EventStore
from app.modules.event.retry.policy import RetryPolicy
from app.modules.event.schemas.records import (
    EventRecord,
    NotificationRecord,
    RetryRecord,
)
from app.modules.event.schemas.status import EventStatus, NotificationStatus


class NotificationWorker:
    """Xử lý gửi notification cho event."""

    def __init__(
        self,
        queue: BoundedQueue[EventRecord],
        registry: ProviderRegistry,
        store: EventStore,
        config: NotificationConfig,
        retry_config: RetryConfig,
        dedup: Optional[DedupCooldown] = None,
        sleeper=None,
    ) -> None:
        self._queue = queue
        self._registry = registry
        self._store = store
        self._config = config
        self._dedup = dedup or DedupCooldown(
            config.dedup_window_seconds, config.cooldown_seconds
        )
        self._retry = RetryPolicy(retry_config, sleeper=sleeper)

    @property
    def dedup(self) -> DedupCooldown:
        return self._dedup

    def drain(self) -> int:
        """Xử lý toàn bộ event đang chờ trong queue. Trả số event đã xử lý."""
        count = 0
        while True:
            record = self._queue.get()
            if record is None:
                break
            self.process(record)
            count += 1
        return count

    def process(self, record: EventRecord, force: bool = False) -> NotificationRecord:
        """Gửi notification cho một event (áp dụng dedup/cooldown trừ khi force)."""
        now = datetime.now(timezone.utc)
        channel = self._config.channel

        if not self._config.enabled:
            return self._finalize(record, self._skipped(channel, "notification_disabled"))

        if not force and not self._dedup.should_send(
            record.rule_id, record.track_id, now
        ):
            logger.info(
                "Notification bỏ qua (dedup/cooldown) rule={} track={}",
                record.rule_id,
                record.track_id,
            )
            return self._finalize(record, self._skipped(channel, "dedup_or_cooldown"))

        provider = self._registry.get(channel)
        if provider is None or not provider.is_ready:
            return self._finalize(record, self._skipped(channel, "provider_not_ready"))

        message = build_alert_message(record)
        notif = NotificationRecord(channel=channel, target=None)

        def _send():
            return provider.send(message)

        def _on_retry(attempt: int, delay: float, error: str) -> None:
            notif.retries.append(RetryRecord(attempt=attempt, delay=delay, error=error))

        outcome = self._retry.run(_send, on_retry=_on_retry)
        notif.attempts = outcome.attempts

        if outcome.ok:
            notif.status = NotificationStatus.SENT
            notif.sent_at = datetime.now(timezone.utc)
            self._dedup.mark_sent(record.rule_id, record.track_id, now)
            record.touch(EventStatus.NOTIFICATION_SENT)
            logger.info("Telegram Sent event={}", record.event_id)
            record.notifications.append(notif)
            record.touch(EventStatus.COMPLETED)
        elif outcome.skipped:
            notif.status = NotificationStatus.SKIPPED
            record.notifications.append(notif)
            record.touch(EventStatus.COMPLETED)
        else:
            notif.status = NotificationStatus.FAILED
            notif.error = outcome.error
            record.error = outcome.error
            record.notifications.append(notif)
            record.touch(EventStatus.FAILED)
            logger.warning(
                "Notification Failed event={} error={}", record.event_id, outcome.error
            )

        self._store.save(record)
        return notif

    def _skipped(self, channel: str, reason: str) -> NotificationRecord:
        return NotificationRecord(
            channel=channel, status=NotificationStatus.SKIPPED, error=reason
        )

    def _finalize(
        self, record: EventRecord, notif: NotificationRecord
    ) -> NotificationRecord:
        record.notifications.append(notif)
        record.touch(EventStatus.COMPLETED)
        self._store.save(record)
        return notif
