"""Tests for Ops module — deep health (Sprint 11)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ops.health import _storage_check, check_full


def test_storage_check_returns_metrics():
    result = _storage_check()
    assert "ok" in result
    assert "percent_used" in result
    assert "free_gb" in result


@pytest.mark.asyncio
async def test_check_full_minimal_app():
    """App không có admin/performance vẫn trả về cấu trúc hợp lệ."""

    class FakeApp:
        state = type("S", (), {})()

    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.get_session_factory", return_value=mock_factory):
        with patch("app.modules.ops.health.check_redis_connection", return_value=True):
            data = await check_full(FakeApp())

    assert data["status"] in {"healthy", "degraded", "unhealthy"}
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "storage" in data["components"]
    assert data["version"] == "1.0.0"
