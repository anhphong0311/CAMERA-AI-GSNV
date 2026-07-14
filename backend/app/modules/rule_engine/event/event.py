"""
DTO — BehaviorEventDTO: đầu ra chuẩn của Rule Engine.

KHÔNG chứa logic Telegram/DB/Dashboard. Sprint 7 sẽ tiêu thụ event này.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.state.event_state import EventState


def new_event_id() -> str:
    """Sinh event_id duy nhất."""
    return uuid.uuid4().hex


@dataclass
class BehaviorEventDTO:
    """
    Sự kiện hành vi do Rule Engine tạo.

    Attributes:
        event_id: ID duy nhất.
        camera_id / track_id: Nguồn.
        rule_id / event_type: Rule sinh ra event (event_type = rule_id).
        severity: Mức nghiêm trọng.
        confidence: Độ tin cậy 0..1 (ước lượng từ feature).
        state: Trạng thái vòng đời.
        start_time / end_time / duration: Thời gian sự kiện.
        snapshot / video_reference: Tham chiếu (Sprint 7 điền; ở đây None).
        metadata: Facts/ngữ cảnh kèm theo.
    """

    camera_id: int
    track_id: int
    rule_id: str
    event_type: str
    severity: Severity
    start_time: datetime
    event_id: str = field(default_factory=new_event_id)
    confidence: float = 0.9
    state: EventState = EventState.NEW
    end_time: Optional[datetime] = None
    duration: float = 0.0
    snapshot: Optional[str] = None
    video_reference: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event."""
        return {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "track_id": self.track_id,
            "rule_id": self.rule_id,
            "event_type": self.event_type,
            "severity": self.severity.value,
            "confidence": round(self.confidence, 4),
            "state": self.state.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": round(self.duration, 2),
            "snapshot": self.snapshot,
            "video_reference": self.video_reference,
            "metadata": self.metadata,
        }
