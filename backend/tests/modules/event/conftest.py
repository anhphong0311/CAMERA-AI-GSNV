"""
Fixtures + builders cho test Event Processing Center (Sprint 7).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pytest

from app.modules.event.config import (
    EventConfig,
    NotificationConfig,
    RecorderConfig,
    RetryConfig,
    SnapshotConfig,
    TelegramConfig,
)
from app.modules.event.notification import MemoryNotificationProvider
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.services import EventService

BASE_TIME = datetime(2026, 7, 5, 9, 15, 22, tzinfo=timezone.utc)


def at(seconds: float) -> datetime:
    """Mốc thời gian tương đối BASE_TIME."""
    return BASE_TIME + timedelta(seconds=seconds)


def make_event(
    *,
    camera_id: int = 1,
    camera_name: Optional[str] = "Office01",
    track_id: int = 12,
    rule_id: str = "PHONE_USAGE",
    severity: str = "HIGH",
    confidence: float = 0.96,
    duration: float = 18.0,
    roi: Optional[str] = "Desk 05",
    start_time: Optional[datetime] = None,
    event_id: Optional[str] = None,
) -> BehaviorEventInput:
    """Tạo BehaviorEventInput mẫu."""
    kwargs = dict(
        camera_id=camera_id,
        camera_name=camera_name,
        track_id=track_id,
        rule_id=rule_id,
        event_type=rule_id,
        severity=severity,
        confidence=confidence,
        duration=duration,
        roi=roi,
        start_time=start_time or BASE_TIME,
    )
    if event_id is not None:
        kwargs["event_id"] = event_id
    return BehaviorEventInput(**kwargs)


def frame(h: int = 48, w: int = 64, value: int = 100) -> np.ndarray:
    """Frame BGR uint8 đồng màu."""
    return np.full((h, w, 3), value, dtype=np.uint8)


def build_service(
    tmp_path,
    *,
    fail_times: int = 0,
    ready: bool = True,
    channel: str = "memory",
    process_video: bool = True,
    process_notification: bool = True,
) -> tuple[EventService, MemoryNotificationProvider]:
    """Dựng EventService dùng MemoryNotificationProvider + thư mục tạm."""
    event_cfg = EventConfig(
        storage_dir=str(tmp_path),
        process_video=process_video,
        process_notification=process_notification,
        history_size=500,
    )
    snap_cfg = SnapshotConfig(dir=str(tmp_path / "snapshots"))
    rec_cfg = RecorderConfig(
        dir=str(tmp_path / "videos"), pre_seconds=10, post_seconds=10, fps=10
    )
    notif_cfg = NotificationConfig(channel=channel)
    tg_cfg = TelegramConfig(retry=RetryConfig(max_attempts=3, backoff=[0, 0, 0]))
    provider = MemoryNotificationProvider(fail_times=fail_times, ready=ready)
    service = EventService(
        event_config=event_cfg,
        snapshot_config=snap_cfg,
        recorder_config=rec_cfg,
        notification_config=notif_cfg,
        telegram_config=tg_cfg,
        provider=provider,
        sleeper=lambda s: None,
    )
    return service, provider


@pytest.fixture
def service_and_provider(tmp_path):
    """EventService + MemoryNotificationProvider sẵn sàng."""
    return build_service(tmp_path)
