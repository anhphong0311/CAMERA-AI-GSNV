"""Tests for Watchdog (Sprint 11)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ops.watchdog import Watchdog


@pytest.mark.asyncio
async def test_watchdog_backend_unreachable():
    wd = Watchdog(backend_url="http://invalid.test", interval_s=1, telegram_token="", telegram_chat_id="")
    with patch.object(wd, "_maybe_alert", new_callable=AsyncMock) as alert:
        data = await wd.check_once()
    assert data["status"] == "unhealthy"
    alert.assert_called_once()


@pytest.mark.asyncio
async def test_watchdog_healthy_response():
    wd = Watchdog(backend_url="http://backend:8000", telegram_token="", telegram_chat_id="")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": {"status": "healthy", "components": {}}}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.modules.ops.watchdog.httpx.AsyncClient", return_value=mock_client):
        with patch.object(wd, "_maybe_alert", new_callable=AsyncMock) as alert:
            data = await wd.check_once()
    assert data["status"] == "healthy"
    alert.assert_not_called()


@pytest.mark.asyncio
async def test_watchdog_alert_cooldown():
    wd = Watchdog(telegram_token="", telegram_chat_id="")
    wd._cooldown_s = 9999
    await wd._maybe_alert("test", "msg1")
    with patch("app.modules.ops.watchdog.logger") as log:
        await wd._maybe_alert("test", "msg2")
        log.warning.assert_not_called()
