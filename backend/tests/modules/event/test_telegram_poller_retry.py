"""A Telegram command remains pending until its reply is delivered."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.modules.event.config import TelegramConfig
from app.modules.event.telegram.poller import TelegramCommandPoller


@pytest.mark.asyncio
async def test_failed_reply_does_not_acknowledge_command():
    poller = TelegramCommandPoller(
        TelegramConfig(enabled=True, bot_token="test-token", chat_id="123"),
        Mock(),
        command_handler=lambda command: "pong",
    )
    poller._send_reply = AsyncMock(side_effect=[False, True])
    update = {"update_id": 42, "message": {"text": "/status", "chat": {"id": 123}}}

    assert await poller._process_update(update) is False
    assert poller._offset is None
    assert await poller._process_update(update) is True
    assert poller._offset == 43


@pytest.mark.asyncio
async def test_non_command_is_acknowledged():
    poller = TelegramCommandPoller(
        TelegramConfig(enabled=True, bot_token="test-token", chat_id="123"),
        Mock(),
        command_handler=lambda command: "pong",
    )
    assert await poller._process_update(
        {"update_id": 7, "message": {"text": "hello", "chat": {"id": 123}}}
    )
    assert poller._offset == 8
