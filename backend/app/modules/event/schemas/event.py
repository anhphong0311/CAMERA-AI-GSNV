"""
BehaviorEventInput — DTO đầu vào của Event Processing Center.

Độc lập với Rule Engine (không import DTO nội bộ). App layer chuyển
BehaviorEventDTO (Sprint 6) → BehaviorEventInput qua `from_dict`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.modules.event.exceptions import InvalidEventError


def _parse_time(value: Any) -> datetime:
    """Parse ISO string / datetime → datetime (UTC-aware)."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


@dataclass
class BehaviorEventInput:
    """
    Event hành vi cần xử lý.

    Attributes:
        event_id: ID duy nhất (từ Rule Engine hoặc tự sinh).
        camera_id / camera_name: Nguồn camera.
        track_id: Người/đối tượng.
        rule_id / event_type: Rule sinh event.
        severity / confidence: Mức độ + độ tin cậy.
        start_time / end_time / duration: Thời gian sự kiện.
        roi: Vùng liên quan.
        metadata: Ngữ cảnh kèm theo.
    """

    camera_id: int
    track_id: int
    rule_id: str
    event_type: str = ""
    severity: str = "INFO"
    confidence: float = 0.0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration: float = 0.0
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    camera_name: Optional[str] = None
    roi: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.event_type:
            self.event_type = self.rule_id

    def validate(self) -> None:
        """Kiểm tra trường bắt buộc."""
        if self.camera_id is None:
            raise InvalidEventError("Thiếu camera_id")
        if self.track_id is None:
            raise InvalidEventError("Thiếu track_id")
        if not self.rule_id:
            raise InvalidEventError("Thiếu rule_id")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BehaviorEventInput":
        """Tạo từ dict (vd BehaviorEventDTO.to_dict())."""
        meta = data.get("metadata") or {}
        roi = data.get("roi")
        if roi is None and isinstance(meta, dict):
            facts = meta.get("facts") if isinstance(meta.get("facts"), dict) else {}
            roi = facts.get("roi")
        evidence_time = data.get("evidence_time")
        if evidence_time is None and isinstance(meta, dict):
            evidence_time = meta.get("evidence_time")
        parsed_evidence = (
            _parse_time(evidence_time) if evidence_time else None
        )
        return cls(
            event_id=str(data.get("event_id") or uuid.uuid4().hex),
            camera_id=int(data["camera_id"]),
            camera_name=data.get("camera_name"),
            track_id=int(data["track_id"]),
            rule_id=str(data["rule_id"]),
            event_type=str(data.get("event_type") or data["rule_id"]),
            severity=str(data.get("severity", "INFO")),
            confidence=float(data.get("confidence", 0.0)),
            start_time=_parse_time(data.get("start_time")),
            end_time=_parse_time(data["end_time"]) if data.get("end_time") else None,
            duration=float(data.get("duration", 0.0)),
            roi=roi,
            metadata=meta if isinstance(meta, dict) else {},
            evidence_time=parsed_evidence,
        )
