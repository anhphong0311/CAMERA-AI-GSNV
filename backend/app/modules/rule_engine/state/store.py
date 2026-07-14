"""
StateStore — quản lý RuleState cho mọi (rule, track); chống memory leak (LRU).
StateMachine — bảng chuyển trạng thái Event hợp lệ.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, Iterable, Optional, Tuple

from loguru import logger

from app.modules.rule_engine.state.event_state import EventState
from app.modules.rule_engine.state.rule_state import RuleState

Key = Tuple[str, int]


class StateStore:
    """Kho RuleState theo (rule_id, track_id), giới hạn số lượng."""

    def __init__(self, max_states: int = 5000) -> None:
        self._states: Dict[Key, RuleState] = {}
        self._max_states = max_states
        self._lock = threading.RLock()

    def get_or_create(
        self, rule_id: str, track_id: int, camera_id: int
    ) -> RuleState:
        """Lấy/tạo state cho (rule, track)."""
        key = (rule_id, track_id)
        with self._lock:
            state = self._states.get(key)
            if state is None:
                self._enforce_capacity()
                state = RuleState(
                    rule_id=rule_id, track_id=track_id, camera_id=camera_id
                )
                self._states[key] = state
            return state

    def _enforce_capacity(self) -> None:
        """Loại state cũ nhất khi vượt giới hạn."""
        while len(self._states) >= self._max_states:
            oldest = min(
                self._states,
                key=lambda k: self._states[k].updated_ts or datetime.min,
            )
            del self._states[oldest]
            logger.warning("StateStore vượt giới hạn → loại {}", oldest)

    def prune_stale(self, now: datetime, max_idle_seconds: float) -> int:
        """Xóa state không cập nhật quá lâu và không có event mở."""
        with self._lock:
            stale = [
                k
                for k, s in self._states.items()
                if s.current_event is None
                and s.updated_ts is not None
                and (now - s.updated_ts).total_seconds() > max_idle_seconds
                and not s.in_cooldown(now)
            ]
            for k in stale:
                del self._states[k]
            return len(stale)

    def all_states(self) -> Iterable[RuleState]:
        """Duyệt toàn bộ state."""
        with self._lock:
            return list(self._states.values())

    @property
    def count(self) -> int:
        """Số state."""
        return len(self._states)

    def clear(self) -> None:
        """Xóa toàn bộ."""
        with self._lock:
            self._states.clear()


# Chuyển trạng thái hợp lệ của Event
_TRANSITIONS: Dict[EventState, set[EventState]] = {
    EventState.NEW: {EventState.ACTIVE, EventState.CONFIRMED, EventState.IGNORED},
    EventState.ACTIVE: {EventState.CONFIRMED, EventState.ENDED, EventState.IGNORED},
    EventState.CONFIRMED: {EventState.ENDED},
    EventState.ENDED: set(),
    EventState.IGNORED: set(),
}


class StateMachine:
    """Kiểm tra/áp dụng chuyển trạng thái Event."""

    @staticmethod
    def can_transition(src: EventState, dst: EventState) -> bool:
        """Chuyển từ src → dst có hợp lệ không."""
        return dst in _TRANSITIONS.get(src, set())

    @staticmethod
    def transition(current: EventState, target: EventState) -> EventState:
        """Trả target nếu hợp lệ, ngược lại giữ nguyên."""
        if StateMachine.can_transition(current, target):
            return target
        return current
