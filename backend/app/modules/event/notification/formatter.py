"""
Formatter — dựng nội dung notification từ EventRecord.

Định dạng cảnh báo AI Employee Monitoring (Telegram).
Giờ hiển thị theo Asia/Ho_Chi_Minh (UTC+7).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from zoneinfo import ZoneInfo

    _DISPLAY_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:  # pragma: no cover — Windows thiếu tzdata
    _DISPLAY_TZ = timezone(timedelta(hours=7), name="UTC+7")

from app.modules.event.notification.provider import NotificationMessage
from app.modules.event.schemas.records import EventRecord
from app.modules.event.utils.naming import camera_label

_RULE_LABELS = {
    "PHONE_USAGE": "Sử dụng điện thoại",
    "PRIVATE_TALKING": "Nói chuyện riêng / làm việc cá nhân",
    "AWAY_FROM_DESK": "Rời khỏi vị trí làm việc",
    "EATING": "Ăn uống tại chỗ",
    "SLEEPING": "Ngủ gật",
    "IDLE": "Lười / không làm việc",
}

# Rule cần khoảng thời gian từ–đến rõ ràng trên thông báo
_RANGE_RULES = frozenset({"PHONE_USAGE", "AWAY_FROM_DESK"})


def _to_local(dt: datetime) -> datetime:
    """Chuẩn hóa datetime → giờ Việt Nam (UTC+7)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_DISPLAY_TZ)


def _fmt_time(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return _to_local(dt).strftime("%H:%M:%S")


def _duration_seconds(record: EventRecord) -> int:
    if record.end_time is not None and record.start_time is not None:
        return max(0, int(round((record.end_time - record.start_time).total_seconds())))
    return max(0, int(round(record.duration)))


def build_alert_message(record: EventRecord) -> NotificationMessage:
    """Tạo message cảnh báo cho một event."""
    cam = record.camera_name or camera_label(record.camera_id, None)
    rule_label = _RULE_LABELS.get(record.rule_id, record.rule_id)
    duration_s = _duration_seconds(record)
    start_s = _fmt_time(record.start_time)
    end_s = _fmt_time(record.end_time)

    lines = [
        "🚨 AI Employee Monitoring",
        "",
        f"📷 Camera : {cam}",
        f"👤 Track ID : {record.track_id}",
        f"⚠ Hành vi : {rule_label}",
    ]

    if record.rule_id == "AWAY_FROM_DESK":
        lines.extend(
            [
                f"🚪 Rời lúc : {start_s}",
                "📷 Khu vực làm việc: KHÔNG có nhân viên",
            ]
        )
        # Chỉ hiện "Quay lại" khi event đã kết thúc và có khoảng thời gian rõ
        finished = (
            getattr(record.status, "value", str(record.status)).upper()
            in {"FINISHED", "ENDED", "CLOSED"}
        )
        if finished and record.end_time is not None and duration_s > 0:
            lines.append(f"🔙 Quay lại : {end_s}")
        else:
            lines.append("🔙 Trạng thái : Chưa quay lại")
        lines.append(f"⏱ Thời lượng : {duration_s} giây")
    elif record.rule_id == "PHONE_USAGE":
        lines.extend(
            [
                f"📱 Từ : {start_s}",
                f"📱 Đến : {end_s}",
                f"⏱ Thời lượng : {duration_s} giây",
                "📷 Ảnh: nhân viên đang sử dụng điện thoại",
            ]
        )
    elif record.rule_id in _RANGE_RULES or record.end_time is not None:
        lines.extend(
            [
                f"🕒 Từ : {start_s}",
                f"🕒 Đến : {end_s}",
                f"⏱ Thời lượng : {duration_s} giây",
            ]
        )
    else:
        lines.extend(
            [
                f"⏱ Thời lượng : {duration_s} giây",
                f"🕒 {start_s}",
            ]
        )

    if record.rule_id == "AWAY_FROM_DESK":
        lines.extend(
            [
                "",
                "📷 Snapshot — bàn làm việc không có nhân viên",
                "📹 Video Evidence",
            ]
        )
    elif record.rule_id == "PHONE_USAGE":
        lines.extend(
            [
                "",
                "📷 Snapshot — nhân viên sử dụng điện thoại",
                "📹 Video Evidence",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "📷 Snapshot",
                "📹 Video Evidence",
            ]
        )
    body = "\n".join(lines)
    return NotificationMessage(
        title="🚨 AI Employee Monitoring",
        body=body,
        event_id=record.event_id,
        snapshot_path=record.snapshot.path if record.snapshot and record.snapshot.path else None,
        video_path=record.video.path if record.video and record.video.path else None,
    )
