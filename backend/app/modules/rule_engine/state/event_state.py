"""
EventState — trạng thái vòng đời của một Event.

Vòng đời: Created(NEW) → Candidate(ACTIVE) → Confirmed(CONFIRMED/Alerted)
→ Resolved(ENDED). IGNORED khi bị cooldown/duplicate loại.
"""

from __future__ import annotations

from enum import Enum


class EventState(str, Enum):
    """Trạng thái vòng đời sự kiện (Rule Engine)."""

    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FINISHED = "FINISHED"
    # Alias tương thích Sprint trước
    NEW = "WAITING"
    ENDED = "FINISHED"
    IGNORED = "CANCELLED"
