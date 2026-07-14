"""
TelegramBot — xử lý command (/start /help /status /cameras /events /latest
+ /bat /tat /system_on /system_off /system_status).

Không tự long-poll trong module này (tránh block); trả nội dung text để tầng
tích hợp gửi đi. Dữ liệu lấy qua callback tiêm vào (decoupled).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, List, Optional, Union

SyncStr = Callable[[], str]
AsyncStr = Callable[[], Awaitable[str]]
MaybeAsyncStr = Union[SyncStr, AsyncStr]


@dataclass
class BotContext:
    """Nguồn dữ liệu cho bot command (callbacks)."""

    status_provider: SyncStr
    cameras_provider: Callable[[], List[str]]
    events_provider: Callable[[int], List[str]]
    latest_provider: SyncStr
    system_on: Optional[AsyncStr] = None
    system_off: Optional[AsyncStr] = None
    system_status: Optional[SyncStr] = None


COMMANDS = [
    "/start",
    "/help",
    "/status",
    "/cameras",
    "/events",
    "/latest",
    "/system_on",
    "/system_off",
    "/system_status",
    "/bat",
    "/tat",
    "/on",
    "/off",
]

_ON_CMDS = frozenset({"/system_on", "/bat", "/on"})
_OFF_CMDS = frozenset({"/system_off", "/tat", "/off"})
_SYS_STATUS_CMDS = frozenset({"/system_status"})


class TelegramBot:
    """Dispatcher command Telegram → text."""

    def __init__(self, context: BotContext) -> None:
        self._ctx = context

    async def handle(self, command: str) -> str:
        """Xử lý một command, trả nội dung text."""
        cmd = (command or "").strip().split()[0].lower() if command.strip() else ""
        if cmd in ("/start", "/help"):
            return self._help()
        if cmd == "/status":
            base = self._ctx.status_provider()
            if self._ctx.system_status is not None:
                return f"{self._ctx.system_status()}\n\n{base}"
            return base
        if cmd in _SYS_STATUS_CMDS:
            if self._ctx.system_status is None:
                return "Chưa gắn System Control."
            return self._ctx.system_status()
        if cmd in _ON_CMDS:
            if self._ctx.system_on is None:
                return "Chưa gắn System Control."
            return await self._ctx.system_on()
        if cmd in _OFF_CMDS:
            if self._ctx.system_off is None:
                return "Chưa gắn System Control."
            return await self._ctx.system_off()
        if cmd == "/cameras":
            cams = self._ctx.cameras_provider()
            return "📷 Danh sách camera:\n" + ("\n".join(cams) if cams else "(chưa có)")
        if cmd == "/events":
            events = self._ctx.events_provider(10)
            return "🗂 Cảnh báo gần đây:\n" + (
                "\n".join(events) if events else "(chưa có)"
            )
        if cmd == "/latest":
            return self._ctx.latest_provider()
        return "Lệnh không hợp lệ. Gõ /help để xem hướng dẫn."

    @staticmethod
    def _help() -> str:
        return (
            "🤖 AEMS Bot — BIBOUS-AI\n"
            "/start, /help — hướng dẫn\n"
            "/bat, /system_on, /on — BẬT toàn bộ hệ thống\n"
            "/tat, /system_off, /off — TẮT toàn bộ hệ thống\n"
            "/system_status — trạng thái bật/tắt giám sát\n"
            "/status — trạng thái tổng hợp\n"
            "/cameras — danh sách camera\n"
            "/events — cảnh báo gần đây\n"
            "/latest — cảnh báo mới nhất"
        )
