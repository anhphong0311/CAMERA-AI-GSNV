"""
DedupCooldown — chống spam notification.

- Dedup: cùng rule + person trong `dedup_window` → không gửi thêm.
- Cooldown: sau khi gửi, khóa (rule, track) trong `cooldown_seconds`.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Dict, Tuple

Key = Tuple[str, int]


class DedupCooldown:
    """Bộ lọc dedup + cooldown theo (rule_id, track_id)."""

    def __init__(self, dedup_window: float, cooldown_seconds: float) -> None:
        self._dedup_window = dedup_window
        self._cooldown = cooldown_seconds
        self._last_sent: Dict[Key, datetime] = {}
        self._cooldown_until: Dict[Key, datetime] = {}
        self._lock = threading.RLock()

    def should_send(self, rule_id: str, track_id: int, now: datetime) -> bool:
        """True nếu được phép gửi (không trùng, không trong cooldown)."""
        key = (rule_id, track_id)
        with self._lock:
            until = self._cooldown_until.get(key)
            if until is not None and now < until:
                return False
            last = self._last_sent.get(key)
            if last is not None and (now - last).total_seconds() < self._dedup_window:
                return False
            return True

    def mark_sent(self, rule_id: str, track_id: int, now: datetime) -> None:
        """Ghi nhận đã gửi → bật cooldown + dedup."""
        key = (rule_id, track_id)
        with self._lock:
            self._last_sent[key] = now
            self._cooldown_until[key] = now + timedelta(seconds=self._cooldown)

    def cleanup(self, now: datetime) -> int:
        """Dọn bản ghi hết hạn."""
        with self._lock:
            horizon = max(self._dedup_window, self._cooldown)
            old = [
                k
                for k, t in self._last_sent.items()
                if (now - t).total_seconds() > horizon
            ]
            for k in old:
                self._last_sent.pop(k, None)
                self._cooldown_until.pop(k, None)
            return len(old)

    def clear(self) -> None:
        with self._lock:
            self._last_sent.clear()
            self._cooldown_until.clear()
