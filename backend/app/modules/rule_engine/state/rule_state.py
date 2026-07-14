"""
RuleState — trạng thái theo dõi của một (rule_id, track_id).

Giữ bộ đếm thời gian điều kiện được thỏa liên tục (phục vụ leaf duration),
event đang mở, và mốc cooldown.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.modules.rule_engine.event.event import BehaviorEventDTO


@dataclass
class RuleState:
    """State cho một cặp (rule, track)."""

    rule_id: str
    track_id: int
    camera_id: int
    active_since: Optional[datetime] = None
    active_seconds: float = 0.0
    confirm_frames: int = 0
    last_ts: Optional[datetime] = None
    updated_ts: Optional[datetime] = None
    current_event: Optional["BehaviorEventDTO"] = None
    cooldown_until: Optional[datetime] = None
    lifecycle: str = "WAITING"
    gap_seconds: float = 0.0
    start_frame_index: Optional[int] = None
    evidence_time: Optional[datetime] = None

    def reset_activity(self) -> None:
        """Reset bộ đếm khi điều kiện nền không còn thỏa."""
        self.active_since = None
        self.active_seconds = 0.0
        self.confirm_frames = 0
        self.gap_seconds = 0.0
        self.start_frame_index = None
        self.evidence_time = None
        if self.lifecycle not in ("CONFIRMED", "FINISHED"):
            self.lifecycle = "WAITING"

    def in_cooldown(self, now: datetime) -> bool:
        """Đang trong thời gian cooldown?"""
        return self.cooldown_until is not None and now < self.cooldown_until
