"""Factory tạo tracker theo config — mở rộng thuật toán không đổi business logic."""

from __future__ import annotations

from app.modules.tracking.config import TrackerConfig
from app.modules.tracking.tracking_engine.base_tracker import BaseTracker


def create_tracker(config: TrackerConfig) -> BaseTracker:
    """
    Tạo tracker theo config.tracker.type.

    Hiện hỗ trợ: bytetrack. Thêm deepsort/ocsort/strongsort = thêm nhánh ở đây,
    KHÔNG đổi TrackManager/Engine/Service/API.

    Args:
        config: TrackerConfig.

    Returns:
        BaseTracker.

    Raises:
        ValueError: Loại tracker chưa hỗ trợ.
    """
    tracker_type = config.type.lower()
    if tracker_type == "bytetrack":
        from app.modules.tracking.bytetrack.adapter import ByteTrackAdapter

        return ByteTrackAdapter(config)
    raise ValueError(f"Loại tracker chưa hỗ trợ: {config.type}")
