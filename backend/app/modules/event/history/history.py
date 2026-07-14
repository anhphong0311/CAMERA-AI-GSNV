"""
History — truy vấn lịch sử Notification & Retry từ EventStore (read model).

Không lưu trùng dữ liệu: notification/retry đã nằm trong EventRecord.
"""

from __future__ import annotations

from typing import Any, List

from app.modules.event.repositories.store import EventStore


def notification_history(store: EventStore, limit: int = 200) -> List[dict[str, Any]]:
    """Danh sách notification gần đây (kèm event_id)."""
    out: List[dict[str, Any]] = []
    for record in store.list(limit=limit):
        for notif in record.notifications:
            item = notif.to_dict()
            item["event_id"] = record.event_id
            item["rule_id"] = record.rule_id
            item["camera_id"] = record.camera_id
            item["track_id"] = record.track_id
            out.append(item)
    return out[-limit:]


def retry_history(store: EventStore, limit: int = 200) -> List[dict[str, Any]]:
    """Danh sách retry gần đây (kèm event_id)."""
    out: List[dict[str, Any]] = []
    for record in store.list(limit=limit):
        for notif in record.notifications:
            for r in notif.retries:
                item = r.to_dict()
                item["event_id"] = record.event_id
                item["channel"] = notif.channel
                out.append(item)
    return out[-limit:]
