"""
Domain records — output chuẩn của Event Processing Center.

EventRecord tổng hợp SnapshotRecord / VideoRecord / NotificationRecord / RetryRecord.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from app.modules.event.schemas.status import EventStatus, NotificationStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return uuid.uuid4().hex


@dataclass
class SnapshotRecord:
    """Ảnh bằng chứng."""

    path: str
    id: str = field(default_factory=_uid)
    width: Optional[int] = None
    height: Optional[int] = None
    status: str = "created"
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class VideoRecord:
    """Video evidence (pre + post event)."""

    path: str
    id: str = field(default_factory=_uid)
    duration_s: float = 0.0
    codec: str = "mp4v"
    status: str = "created"
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "duration_s": round(self.duration_s, 2),
            "codec": self.codec,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RetryRecord:
    """Một lần retry gửi notification."""

    attempt: int
    delay: float
    error: Optional[str] = None
    id: str = field(default_factory=_uid)
    at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "attempt": self.attempt,
            "delay": self.delay,
            "error": self.error,
            "at": self.at.isoformat(),
        }


@dataclass
class NotificationRecord:
    """Log gửi notification."""

    channel: str
    target: Optional[str] = None
    id: str = field(default_factory=_uid)
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    error: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=_now)
    retries: List[RetryRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "target": self.target,
            "status": self.status.value,
            "attempts": self.attempts,
            "error": self.error,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat(),
            "retries": [r.to_dict() for r in self.retries],
        }


@dataclass
class EventRecord:
    """Bản ghi xử lý một event (evidence + notification + trạng thái)."""

    event_id: str
    camera_id: int
    track_id: int
    rule_id: str
    event_type: str
    severity: str
    confidence: float
    start_time: datetime
    camera_name: Optional[str] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0
    roi: Optional[str] = None
    status: EventStatus = EventStatus.NEW
    snapshot: Optional[SnapshotRecord] = None
    video: Optional[VideoRecord] = None
    notifications: List[NotificationRecord] = field(default_factory=list)
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def touch(self, status: Optional[EventStatus] = None) -> None:
        """Cập nhật thời điểm + trạng thái."""
        if status is not None:
            self.status = status
        self.updated_at = _now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "track_id": self.track_id,
            "rule_id": self.rule_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "confidence": round(self.confidence, 4),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": round(self.duration, 2),
            "roi": self.roi,
            "status": self.status.value,
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "video": self.video.to_dict() if self.video else None,
            "notifications": [n.to_dict() for n in self.notifications],
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
