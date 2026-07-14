"""Exceptions package — Event Processing Center."""

from app.modules.event.exceptions.errors import (
    DiskFullError,
    EventNotFoundError,
    EventProcessingException,
    InvalidEventError,
    NotificationError,
    RecorderError,
    SnapshotError,
    TelegramError,
)

__all__ = [
    "DiskFullError",
    "EventNotFoundError",
    "EventProcessingException",
    "InvalidEventError",
    "NotificationError",
    "RecorderError",
    "SnapshotError",
    "TelegramError",
]
