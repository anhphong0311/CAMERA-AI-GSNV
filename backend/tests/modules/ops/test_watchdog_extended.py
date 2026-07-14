"""Watchdog extended tests (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.modules.ops import watchdog


@pytest.mark.asyncio
async def test_watchdog_telegram_alert_sent():
    wd = watchdog.Watchdog(
        backend_url="http://x",
        telegram_token="tok",
        telegram_chat_id="123",
    )
    mock_client = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.modules.ops.watchdog.httpx.AsyncClient", return_value=mock_client):
        await wd._maybe_alert("disk", "Disk full")
    mock_client.post.assert_called_once()


def test_watchdog_main_exits_on_keyboard_interrupt():
    with patch.object(watchdog.asyncio, "run", side_effect=KeyboardInterrupt):
        with pytest.raises(SystemExit) as exc:
            watchdog.main()
        assert exc.value.code == 0
