"""
RuleScheduler — điều phối bảo trì định kỳ (cleanup cache/state/temporal).

Rule Engine gọi tick(now) mỗi frame; scheduler chạy callback dọn dẹp theo chu kỳ
để tránh memory leak mà không chặn luồng xử lý.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, List, Optional


class RuleScheduler:
    """Chạy các tác vụ bảo trì theo chu kỳ (giây)."""

    def __init__(self, interval_seconds: float = 30.0) -> None:
        self._interval = interval_seconds
        self._last_run: Optional[datetime] = None
        self._tasks: List[Callable[[datetime], None]] = []

    def add_task(self, task: Callable[[datetime], None]) -> None:
        """Thêm callback bảo trì (nhận `now`)."""
        self._tasks.append(task)

    def tick(self, now: datetime) -> bool:
        """
        Chạy tác vụ nếu đã đủ chu kỳ.

        Returns:
            True nếu đã chạy bảo trì lần này.
        """
        if self._last_run is not None and (
            now - self._last_run
        ).total_seconds() < self._interval:
            return False
        self._last_run = now
        for task in self._tasks:
            task(now)
        return True
