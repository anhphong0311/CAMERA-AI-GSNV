"""
TelegramProvider — gửi cảnh báo qua Telegram Bot API (httpx).

Đính kèm Snapshot (sendPhoto) và Video (sendVideo). Nếu chưa cấu hình
token/chat_id → skipped (không retry). Lỗi mạng/timeout → raise TelegramError.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.modules.event.config import TelegramConfig
from app.modules.event.exceptions import TelegramError
from app.modules.event.notification.provider import (
    NotificationMessage,
    NotificationProvider,
    SendResult,
)


class TelegramProvider(NotificationProvider):
    """Kênh gửi Telegram."""

    def __init__(self, config: TelegramConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def is_ready(self) -> bool:
        return self._config.is_ready

    def _url(self, method: str) -> str:
        return f"{self._config.api_base}/bot{self._config.bot_token}/{method}"

    def send(self, message: NotificationMessage) -> SendResult:
        """Gửi message + đính kèm evidence."""
        if not self.is_ready:
            return SendResult(ok=False, skipped=True, target=self._config.chat_id or None)
        has_media = (
            message.snapshot_path and Path(message.snapshot_path).exists()
        ) or (message.video_path and Path(message.video_path).exists())
        if has_media:
            return self._send_with_media(message)
        return self.send_text(self._config.chat_id, message.body)

    def send_text(self, chat_id: str, text: str) -> SendResult:
        """Gửi tin nhắn text tới một chat."""
        if not self._config.bot_token:
            return SendResult(ok=False, skipped=True, target=chat_id)

        try:
            import httpx  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise TelegramError(f"httpx không khả dụng: {exc}") from exc

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                resp = client.post(
                    self._url("sendMessage"),
                    data={"chat_id": chat_id, "text": text},
                )
                self._check(resp)
                return SendResult(ok=True, target=chat_id)
        except TelegramError:
            raise
        except Exception as exc:
            raise TelegramError(f"Gửi Telegram lỗi: {exc}") from exc

    def _send_with_media(self, message: NotificationMessage) -> SendResult:
        """Gửi kèm snapshot/video (dùng bởi send khi có file)."""
        if not self.is_ready:
            return SendResult(ok=False, skipped=True, target=self._config.chat_id or None)

        try:
            import httpx  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise TelegramError(f"httpx không khả dụng: {exc}") from exc

        chat_id = self._config.chat_id
        timeout = self._config.timeout_seconds
        try:
            with httpx.Client(timeout=timeout) as client:
                sent_photo = False
                if (
                    self._config.send_snapshot
                    and message.snapshot_path
                    and Path(message.snapshot_path).exists()
                ):
                    with open(message.snapshot_path, "rb") as fh:
                        resp = client.post(
                            self._url("sendPhoto"),
                            data={"chat_id": chat_id, "caption": message.body},
                            files={"photo": fh},
                        )
                    self._check(resp)
                    sent_photo = True
                else:
                    resp = client.post(
                        self._url("sendMessage"),
                        data={"chat_id": chat_id, "text": message.body},
                    )
                    self._check(resp)

                if (
                    self._config.send_video
                    and message.video_path
                    and Path(message.video_path).exists()
                ):
                    with open(message.video_path, "rb") as fh:
                        resp = client.post(
                            self._url("sendVideo"),
                            data={"chat_id": chat_id},
                            files={"video": fh},
                        )
                    self._check(resp)

                logger.info(
                    "Telegram sent event={} (photo={})", message.event_id, sent_photo
                )
                return SendResult(ok=True, target=chat_id)
        except TelegramError:
            raise
        except Exception as exc:  # network/timeout
            raise TelegramError(f"Gửi Telegram lỗi: {exc}") from exc

    @staticmethod
    def _check(resp) -> None:
        """Kiểm tra HTTP response của Telegram."""
        if resp.status_code >= 500:
            raise TelegramError(f"Telegram server {resp.status_code}")
        data = {}
        try:
            data = resp.json()
        except Exception:  # pragma: no cover
            pass
        if not data.get("ok", resp.status_code < 400):
            raise TelegramError(
                f"Telegram API lỗi: {data.get('description', resp.status_code)}"
            )
