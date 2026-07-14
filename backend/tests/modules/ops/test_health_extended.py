"""Extended ops health tests (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ops.health import check_full


@pytest.mark.asyncio
async def test_check_full_with_admin_and_performance():
    class AdminHealth:
        async def check_all(self):
            return {
                "components": {
                    "api": {"ok": True},
                    "telegram": {"ok": True},
                }
            }

    class GpuMgr:
        def snapshot(self):
            return [{"id": 0, "name": "mock"}]

    class Scheduler:
        def summary(self):
            return {"skipped": 0}

    class Orchestrator:
        def stats(self):
            return {"processed": 1}

    class Perf:
        gpu_manager = GpuMgr()
        frame_scheduler = Scheduler()
        orchestrator = Orchestrator()

    class Ai:
        def get_statistics(self):
            return {"pipeline_running": True, "model_loaded": True}

    class CamMgr:
        _workers = {1: MagicMock(is_running=True)}

    class State:
        admin = type("A", (), {"health": AdminHealth()})()
        performance = Perf()
        ai_service = Ai()
        camera_manager = CamMgr()

    class App:
        state = State()

    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("app.core.database.get_session_factory", return_value=mock_factory):
        with patch("app.modules.ops.health.check_redis_connection", return_value=True):
            data = await check_full(App())

    assert data["status"] in {"healthy", "degraded"}
    assert data["components"]["ai_worker"]["ok"] is True
    assert data["components"]["camera"]["online"] == 1
