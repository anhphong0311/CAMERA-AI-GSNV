"""
Tiện ích đặt tên evidence.

Ví dụ: Office01_TRACK12_PHONE_20260705_091522.jpg
"""

from __future__ import annotations

import re
from datetime import datetime

_SAFE = re.compile(r"[^A-Za-z0-9]+")
_SAFE_RULE = re.compile(r"[^A-Za-z0-9_]+")


def sanitize(text: str) -> str:
    """Chuẩn hóa chuỗi cho tên file (bỏ ký tự đặc biệt)."""
    cleaned = _SAFE.sub("", str(text))
    return cleaned or "NA"


def camera_label(camera_id: int, camera_name: str | None) -> str:
    """Nhãn camera cho tên file."""
    if camera_name:
        return sanitize(camera_name)
    return f"CAM{camera_id:02d}"


def rule_label(rule_id: str) -> str:
    """Nhãn rule cho tên file (giữ dấu gạch dưới)."""
    cleaned = _SAFE_RULE.sub("", str(rule_id)).upper()
    return cleaned or "NA"


def build_evidence_name(
    camera_id: int,
    camera_name: str | None,
    track_id: int,
    rule_id: str,
    timestamp: datetime,
    ext: str,
) -> str:
    """
    Dựng tên file evidence chuẩn.

    Args:
        ext: đuôi file không dấu chấm (jpg/mp4).

    Returns:
        vd Office01_TRACK12_PHONE_USAGE_20260705_091522.jpg
    """
    cam = camera_label(camera_id, camera_name)
    ts = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{cam}_TRACK{track_id}_{rule_label(rule_id)}_{ts}.{ext.lstrip('.')}"
