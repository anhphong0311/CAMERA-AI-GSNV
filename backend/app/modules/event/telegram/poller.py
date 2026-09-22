"""
TelegramCommandPoller — long-poll getUpdates và trả lời lệnh bot.

Chạy asyncio task nền; không block camera/AI pipeline.
Chỉ chấp nhận lệnh từ chat_id đã cấu hình (nhóm bot).
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Awaitable, Callable, Optional, Union

from loguru import logger

from app.modules.event.config import TelegramConfig
from app.modules.event.services.event_service import EventService

CommandHandler = Callable[..., Union[str, Awaitable[str]]]


class TelegramCommandPoller:
    """Nhận lệnh từ Telegram và gửi phản hồi text."""

    def __init__(
        self,
        config: TelegramConfig,
        service: EventService,
        *,
        command_handler: CommandHandler,
    ) -> None:
        self._config = config
        self._service = service
        self._handle = command_handler
        self._offset: Optional[int] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_poll_error_log = 0.0

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running or not self._config.is_ready:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Telegram command poller started")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Telegram command poller stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                updates = await asyncio.to_thread(self._fetch_updates)
                for upd in updates:
                    if not await self._process_update(upd):
                        await asyncio.sleep(10.0)
                        break
            except asyncio.CancelledError:
                break
            except Exception as exc:
                now = time.monotonic()
                if now - self._last_poll_error_log >= 60.0:
                    logger.warning(
                        "Telegram command polling unavailable | error_type={}",
                        type(exc).__name__,
                    )
                    self._last_poll_error_log = now
                await asyncio.sleep(3.0)

    def _fetch_updates(self) -> list[dict[str, Any]]:
        import httpx

        params: dict[str, Any] = {"timeout": 25}
        if self._offset is not None:
            params["offset"] = self._offset
        url = (
            f"{self._config.api_base}/bot{self._config.bot_token}/getUpdates"
        )
        with httpx.Client(timeout=35.0) as client:
            resp = client.get(url, params=params)
            data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "getUpdates failed"))
        return data.get("result") or []

    def _is_allowed_chat(self, chat_id: Any) -> bool:
        allowed = str(self._config.chat_id or "").strip()
        if not allowed:
            return False
        return str(chat_id).strip() == allowed

    async def _process_update(self, update: dict[str, Any]) -> bool:
        uid = update.get("update_id")
        next_offset = int(uid) + 1 if uid is not None else self._offset

        message = update.get("message") or update.get("edited_message")
        if not message:
            self._offset = next_offset
            return True
        text = (message.get("text") or "").strip()
        if not text.startswith("/"):
            self._offset = next_offset
            return True

        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            self._offset = next_offset
            return True

        if not self._is_allowed_chat(chat_id):
            logger.warning(
                "Telegram command ignored from unauthorized chat_id={}",
                chat_id,
            )
            self._offset = next_offset
            return True

        cmd = text.split("@")[0]
        try:
            result = self._handle(cmd)
            if inspect.isawaitable(result):
                reply = await result
            else:
                reply = result
        except Exception as exc:
            logger.exception("Telegram command failed: {}", cmd)
            reply = f"⚠️ Lỗi xử lý lệnh: {exc}"

        if not await self._send_reply(str(chat_id), reply):
            return False
        self._offset = next_offset
        return True

    async def _send_reply(self, chat_id: str, reply: str) -> bool:
        """Deliver command replies reliably when Telegram DNS/network blips."""
        last_error: Optional[Exception] = None
        for attempt, delay in enumerate((1.0, 3.0, 5.0), start=1):
            try:
                result = await asyncio.to_thread(
                    self._service.send_telegram_text, chat_id, reply
                )
                if result.ok:
                    logger.info("Telegram command reply sent (attempt={})", attempt)
                    return True
                last_error = RuntimeError("Telegram command reply was not delivered")
            except Exception as exc:  # network / DNS failures are transient
                last_error = exc
                logger.warning(
                    "Telegram command reply failed (attempt={}/3) | error_type={}",
                    attempt,
                    type(exc).__name__,
                )
            if attempt < 3:
                await asyncio.sleep(delay)

        logger.error(
            "Telegram command reply pending retry | error_type={}",
            type(last_error).__name__,
        )
        return False
