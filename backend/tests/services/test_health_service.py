"""Tests for HealthService (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.health_service import HealthService


@pytest.mark.asyncio
async def test_health_all_ok():
    session = AsyncMock()
    session.execute = AsyncMock()
    with patch("app.services.health_service.check_redis_connection", return_value=True):
        data = await HealthService(session).check()
    assert data.status == "healthy"
    assert data.postgres is True
    assert data.redis is True


@pytest.mark.asyncio
async def test_health_postgres_down():
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=RuntimeError("db down"))
    with patch("app.services.health_service.check_redis_connection", return_value=True):
        data = await HealthService(session).check()
    assert data.status == "unhealthy"
    assert data.postgres is False


@pytest.mark.asyncio
async def test_health_redis_down():
    session = AsyncMock()
    session.execute = AsyncMock()
    with patch("app.services.health_service.check_redis_connection", return_value=False):
        data = await HealthService(session).check()
    assert data.status == "degraded"
    assert data.redis is False
