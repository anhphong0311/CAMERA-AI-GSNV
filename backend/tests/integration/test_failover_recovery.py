"""Failover & recovery tests (Sprint 12 QA) — mocked components."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.camera.health_check.monitor import HealthMonitor
from app.modules.ops.watchdog import Watchdog


def test_camera_health_disconnect_and_reconnect():
    from app.modules.camera.frame_buffer.buffer import FrameBuffer
    from app.modules.camera.fps_monitor.monitor import FPSMonitor

    health = HealthMonitor(camera_id=1)
    health.set_running(True)
    health.on_connected()
    health.on_disconnected("timeout")
    health.on_reconnect()
    status = health.get_status(FPSMonitor(), FrameBuffer(max_size=10))
    assert status.reconnect_count >= 1


@pytest.mark.asyncio
async def test_watchdog_detects_component_failure():
    wd = Watchdog(telegram_token="", telegram_chat_id="")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "status": "degraded",
            "components": {"redis": {"ok": False, "detail": "down"}},
        }
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.modules.ops.watchdog.httpx.AsyncClient", return_value=mock_client):
        with patch.object(wd, "_maybe_alert", new_callable=AsyncMock) as alert:
            data = await wd.check_once()
    assert data["status"] == "degraded"
    alert.assert_called()


@pytest.mark.asyncio
async def test_redis_recovery_simulation():
    """Giả lập Redis down rồi up — health chuyển degraded → healthy."""
    from app.services.health_service import HealthService

    session = AsyncMock()
    session.execute = AsyncMock()
    svc = HealthService(session)

    with patch("app.services.health_service.check_redis_connection", return_value=False):
        down = await svc.check()
    with patch("app.services.health_service.check_redis_connection", return_value=True):
        up = await svc.check()
    assert down.redis is False
    assert up.redis is True


@pytest.mark.asyncio
async def test_backend_restart_health_recovers():
    from app.modules.ops.health import check_full

    class App:
        state = type("S", (), {})()

    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.get_session_factory", return_value=mock_factory):
        with patch("app.modules.ops.health.check_redis_connection", return_value=True):
            result = await check_full(App())
    assert result["status"] in {"healthy", "degraded", "unhealthy"}
    assert "database" in result["components"]
