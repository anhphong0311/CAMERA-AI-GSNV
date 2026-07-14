"""
RetryPolicy — điều khiển retry với backoff (1s, 5s, 10s...).

Sleeper tách rời để test không phải chờ thật (inject sleeper=lambda s: None).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from loguru import logger

from app.modules.event.config import RetryConfig


@dataclass
class RetryOutcome:
    """Kết quả sau khi retry."""

    ok: bool
    attempts: int
    skipped: bool = False
    error: Optional[str] = None


class RetryPolicy:
    """Thực thi một tác vụ có retry + backoff."""

    def __init__(
        self,
        config: RetryConfig,
        sleeper: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._config = config
        self._sleep = sleeper or time.sleep

    def run(self, task: Callable[[], "object"], on_retry=None) -> RetryOutcome:
        """
        Chạy `task()` với retry.

        task() trả về đối tượng có thuộc tính `ok`/`skipped` (SendResult) hoặc
        raise exception → coi là lỗi tạm thời và retry.

        Args:
            on_retry: callback(attempt:int, delay:float, error:str) ghi lịch sử.
        """
        last_error: Optional[str] = None
        attempts = 0
        for attempt in range(1, self._config.max_attempts + 1):
            attempts = attempt
            try:
                result = task()
                skipped = bool(getattr(result, "skipped", False))
                ok = bool(getattr(result, "ok", False))
                if skipped:
                    return RetryOutcome(ok=False, attempts=attempt, skipped=True)
                if ok:
                    return RetryOutcome(ok=True, attempts=attempt)
                last_error = getattr(result, "error", None) or "unknown"
            except Exception as exc:  # lỗi tạm thời → retry
                last_error = str(exc)
                logger.warning("Retry attempt {} lỗi: {}", attempt, last_error)

            if attempt < self._config.max_attempts:
                delay = self._config.delay_for(attempt)
                if on_retry:
                    on_retry(attempt, delay, last_error)
                self._sleep(delay)

        return RetryOutcome(ok=False, attempts=attempts, error=last_error)
