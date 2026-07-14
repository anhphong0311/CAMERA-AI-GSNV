"""
Cooldown & Duplicate filter — chống spam alert và event trùng.

- CooldownCache: sau khi event kết thúc, khóa (rule, track) trong N giây.
- DuplicateFilter: cùng rule + track trong cửa sổ → không tạo event mới.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Dict, Tuple

Key = Tuple[str, int]


class CooldownCache:
    """Quản lý cooldown theo (rule_id, track_id)."""

    def __init__(self) -> None:
        self._until: Dict[Key, datetime] = {}
        self._lock = threading.RLock()

    def start(self, rule_id: str, track_id: int, now: datetime, seconds: float) -> None:
        """Bắt đầu cooldown."""
        with self._lock:
            self._until[(rule_id, track_id)] = now + timedelta(seconds=seconds)

    def active(self, rule_id: str, track_id: int, now: datetime) -> bool:
        """Đang trong cooldown?"""
        with self._lock:
            until = self._until.get((rule_id, track_id))
            return until is not None and now < until

    def cleanup(self, now: datetime) -> int:
        """Xóa cooldown đã hết hạn."""
        with self._lock:
            expired = [k for k, u in self._until.items() if now >= u]
            for k in expired:
                del self._until[k]
            return len(expired)

    def clear(self) -> None:
        with self._lock:
            self._until.clear()


class DuplicateFilter:
    """Lọc event trùng theo (rule_id, track_id) trong cửa sổ thời gian."""

    def __init__(self, window_seconds: float = 300.0) -> None:
        self._window = window_seconds
        self._last: Dict[Key, datetime] = {}
        self._lock = threading.RLock()

    def is_duplicate(self, rule_id: str, track_id: int, now: datetime) -> bool:
        """True nếu vừa tạo event cùng key trong cửa sổ."""
        with self._lock:
            last = self._last.get((rule_id, track_id))
            return last is not None and (now - last).total_seconds() < self._window

    def record(self, rule_id: str, track_id: int, now: datetime) -> None:
        """Ghi nhận thời điểm tạo event."""
        with self._lock:
            self._last[(rule_id, track_id)] = now

    def cleanup(self, now: datetime) -> int:
        """Xóa bản ghi ngoài cửa sổ."""
        with self._lock:
            old = [
                k
                for k, t in self._last.items()
                if (now - t).total_seconds() >= self._window
            ]
            for k in old:
                del self._last[k]
            return len(old)

    def clear(self) -> None:
        with self._lock:
            self._last.clear()
