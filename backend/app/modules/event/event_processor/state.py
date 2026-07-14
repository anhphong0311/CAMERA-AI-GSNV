"""
EventStateMachine — kiểm soát chuyển trạng thái xử lý event.

NEW → VALIDATING → PROCESSING → SNAPSHOT_CREATED → VIDEO_CREATED
→ NOTIFICATION_SENT → COMPLETED. Bất kỳ trạng thái nào → FAILED.
"""

from __future__ import annotations

from typing import Dict, Set

from app.modules.event.schemas.status import EventStatus

_ORDER = [
    EventStatus.NEW,
    EventStatus.VALIDATING,
    EventStatus.PROCESSING,
    EventStatus.SNAPSHOT_CREATED,
    EventStatus.VIDEO_CREATED,
    EventStatus.NOTIFICATION_SENT,
    EventStatus.COMPLETED,
]

_TRANSITIONS: Dict[EventStatus, Set[EventStatus]] = {}
for _i, _s in enumerate(_ORDER):
    nxt: Set[EventStatus] = {EventStatus.FAILED}
    if _i + 1 < len(_ORDER):
        nxt.add(_ORDER[_i + 1])
    # cho phép nhảy tới COMPLETED (khi bỏ qua notification) & tới NOTIFICATION_SENT
    nxt.add(EventStatus.COMPLETED)
    nxt.add(EventStatus.NOTIFICATION_SENT)
    _TRANSITIONS[_s] = nxt
_TRANSITIONS[EventStatus.COMPLETED] = set()
_TRANSITIONS[EventStatus.FAILED] = set()


class EventStateMachine:
    """Kiểm tra chuyển trạng thái event."""

    @staticmethod
    def order() -> list[EventStatus]:
        """Chuỗi trạng thái chuẩn."""
        return list(_ORDER)

    @staticmethod
    def can_transition(src: EventStatus, dst: EventStatus) -> bool:
        """Chuyển src → dst hợp lệ?"""
        return dst in _TRANSITIONS.get(src, set())
