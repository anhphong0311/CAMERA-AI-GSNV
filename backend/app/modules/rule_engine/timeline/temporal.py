"""
TemporalTracker — theo dõi trạng thái điều kiện qua nhiều cửa sổ thời gian.

Giúp phân tích "đã bao lâu" một điều kiện đúng để tránh alert sai. Lưu tỉ lệ
active trong các cửa sổ (10s/30s/1m/5m/10m/30m...) cho mỗi (rule, track).
"""

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Tuple

Key = Tuple[str, int]


class TemporalTracker:
    """Lưu lịch sử (timestamp, active) và tính tỉ lệ active theo cửa sổ."""

    def __init__(self, windows: List[int], max_samples: int = 2000) -> None:
        self._windows = sorted(windows)
        self._max_samples = max_samples
        self._history: Dict[Key, Deque[Tuple[datetime, bool]]] = {}
        self._lock = threading.RLock()

    def record(self, rule_id: str, track_id: int, now: datetime, active: bool) -> None:
        """Ghi nhận trạng thái active của điều kiện nền."""
        key = (rule_id, track_id)
        with self._lock:
            dq = self._history.get(key)
            if dq is None:
                dq = deque(maxlen=self._max_samples)
                self._history[key] = dq
            dq.append((now, active))
            self._trim(dq, now)

    def active_ratio(
        self, rule_id: str, track_id: int, now: datetime, window_seconds: int
    ) -> float:
        """Tỉ lệ frame active trong cửa sổ (0..1)."""
        key = (rule_id, track_id)
        with self._lock:
            dq = self._history.get(key)
            if not dq:
                return 0.0
            total = 0
            active = 0
            for ts, is_active in dq:
                if (now - ts).total_seconds() <= window_seconds:
                    total += 1
                    if is_active:
                        active += 1
            return active / total if total else 0.0

    def windows(self) -> List[int]:
        """Danh sách cửa sổ đang theo dõi."""
        return list(self._windows)

    def summary(self, rule_id: str, track_id: int, now: datetime) -> Dict[str, float]:
        """Tỉ lệ active cho mọi cửa sổ."""
        return {
            f"{w}s": round(self.active_ratio(rule_id, track_id, now, w), 3)
            for w in self._windows
        }

    def _trim(self, dq: Deque[Tuple[datetime, bool]], now: datetime) -> None:
        """Bỏ mẫu cũ hơn cửa sổ lớn nhất."""
        if not self._windows:
            return
        max_window = self._windows[-1]
        while dq and (now - dq[0][0]).total_seconds() > max_window:
            dq.popleft()

    def prune(self, now: datetime) -> int:
        """Xóa key rỗng."""
        with self._lock:
            empty = [k for k, dq in self._history.items() if not dq]
            for k in empty:
                del self._history[k]
            return len(empty)

    def clear(self) -> None:
        with self._lock:
            self._history.clear()
