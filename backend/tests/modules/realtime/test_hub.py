"""Tests for Realtime WebSocket hub (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.realtime.hub import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.mark.asyncio
async def test_connect_disconnect(manager):
    ws = AsyncMock()
    await manager.connect(ws)
    assert manager.active == 1
    assert manager.total_connected == 1
    await manager.disconnect(ws)
    assert manager.active == 0


@pytest.mark.asyncio
async def test_broadcast_sends_to_clients(manager):
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await manager.connect(ws1)
    await manager.connect(ws2)
    await manager.broadcast({"channel": "test", "data": 1})
    ws1.send_json.assert_called_once()
    ws2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_removes_dead_clients(manager):
    ws_ok = AsyncMock()
    ws_dead = AsyncMock()
    ws_dead.send_json.side_effect = RuntimeError("closed")
    await manager.connect(ws_ok)
    await manager.connect(ws_dead)
    await manager.broadcast({"channel": "test"})
    assert manager.active == 1


@pytest.mark.asyncio
async def test_send_personal_disconnects_on_error(manager):
    ws = AsyncMock()
    ws.send_json.side_effect = RuntimeError("closed")
    await manager.connect(ws)
    await manager.send_personal(ws, {"x": 1})
    assert manager.active == 0
