"""Notification package — Event Processing Center."""

from app.modules.event.notification.dedup import DedupCooldown
from app.modules.event.notification.formatter import build_alert_message
from app.modules.event.notification.provider import (
    MemoryNotificationProvider,
    NotificationMessage,
    NotificationProvider,
    SendResult,
)
from app.modules.event.notification.registry import ProviderRegistry
from app.modules.event.notification.worker import NotificationWorker

__all__ = [
    "DedupCooldown",
    "MemoryNotificationProvider",
    "NotificationMessage",
    "NotificationProvider",
    "NotificationWorker",
    "ProviderRegistry",
    "SendResult",
    "build_alert_message",
]
