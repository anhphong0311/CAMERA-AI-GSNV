"""
EventStatus — vòng đời xử lý một event trong Event Processing Center.

NEW → VALIDATING → PROCESSING → SNAPSHOT_CREATED → VIDEO_CREATED
→ NOTIFICATION_SENT → COMPLETED ; lỗi → FAILED.
"""

from __future__ import annotations

from enum import Enum


class EventStatus(str, Enum):
    """Trạng thái xử lý event."""

    NEW = "NEW"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    VIDEO_CREATED = "VIDEO_CREATED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VIDEO_PENDING = "VIDEO_PENDING"


class NotificationStatus(str, Enum):
    """Trạng thái một notification."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
