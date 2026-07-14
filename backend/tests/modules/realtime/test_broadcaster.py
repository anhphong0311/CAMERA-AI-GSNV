"""Tests for RealtimeBroadcaster and metrics (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.realtime.broadcaster import RealtimeBroadcaster
from app.modules.realtime.demo import DemoStream
from app.modules.realtime.hub import ConnectionManager
from app.modules.realtime.metrics import collect_system_metrics


def test_demo_stream_generates_frames():
    demo = DemoStream(cameras=2)
    assert demo.cameras() == [1, 2]
    det = demo.detection_frame(1)
    assert det["camera_id"] == 1
    assert "objects" in det
    trk = demo.tracking_frame(1)
    assert trk["camera_id"] == 1


def test_collect_system_metrics():
    try:
        import psutil  # noqa: F401
        metrics = collect_system_metrics()
        assert "cpu_percent" in metrics
        assert "ram_percent" in metrics
    except ImportError:
        metrics = collect_system_metrics()
        assert metrics["cpu_percent"] is None


@pytest.mark.asyncio
async def test_broadcaster_tick_with_demo():
    mgr = ConnectionManager()
    bc = RealtimeBroadcaster(mgr, interval=0.01)
    with patch.object(mgr, "broadcast", new_callable=AsyncMock) as broadcast:
        await bc._tick()
    assert broadcast.await_count >= 1
    overview = bc.overview()
    assert "cameras_total" in overview
    assert "system" in overview


@pytest.mark.asyncio
async def test_broadcaster_start_stop():
    mgr = ConnectionManager()
    bc = RealtimeBroadcaster(mgr, interval=0.05)
    with patch.object(bc, "_tick", new_callable=AsyncMock):
        bc.start()
        assert bc._task is not None
        await bc.stop()
        assert bc._task is None


def test_broadcaster_recent_alerts():
    mgr = ConnectionManager()
    bc = RealtimeBroadcaster(mgr)
    bc._recent_alerts.appendleft({"id": "a1"})
    assert bc.recent_alerts(10)[0]["id"] == "a1"
