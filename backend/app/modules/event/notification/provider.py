"""
Notification Provider — interface kênh gửi + kết quả gửi.

Thiết kế Provider để sau này thêm Email/Slack/Teams/Discord mà KHÔNG sửa
business logic (Open/Closed). Telegram là một implementation.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NotificationMessage:
    """Nội dung một notification (độc lập kênh)."""

    title: str
    body: str
    event_id: str
    snapshot_path: Optional[str] = None
    video_path: Optional[str] = None


@dataclass
class SendResult:
    """Kết quả gửi qua provider."""

    ok: bool
    skipped: bool = False
    target: Optional[str] = None
    error: Optional[str] = None


class NotificationProvider(ABC):
    """Kênh gửi notification."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên kênh (telegram/email/...)."""

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Provider đã sẵn sàng gửi chưa (cấu hình đủ)."""

    @abstractmethod
    def send(self, message: NotificationMessage) -> SendResult:
        """
        Gửi message.

        Returns:
            SendResult. Nếu chưa sẵn sàng → skipped=True (không retry).

        Raises:
            NotificationError/TelegramError: lỗi tạm thời (worker sẽ retry).
        """


class MemoryNotificationProvider(NotificationProvider):
    """Provider ghi nhớ (test/dev). Có thể mô phỏng lỗi N lần đầu."""

    def __init__(self, fail_times: int = 0, ready: bool = True) -> None:
        self._fail_times = fail_times
        self._ready = ready
        self.sent: List[NotificationMessage] = []
        self.attempts = 0
        self._lock = threading.RLock()

    @property
    def name(self) -> str:
        return "memory"

    @property
    def is_ready(self) -> bool:
        return self._ready

    def send(self, message: NotificationMessage) -> SendResult:
        from app.modules.event.exceptions import NotificationError

        with self._lock:
            if not self._ready:
                return SendResult(ok=False, skipped=True, target="memory")
            self.attempts += 1
            if self.attempts <= self._fail_times:
                raise NotificationError(f"Lỗi giả lập lần {self.attempts}")
            self.sent.append(message)
            return SendResult(ok=True, target="memory")
