"""Camera connection alerts: grace period, deduplication and recovery."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.modules.camera.health_check.telegram_alerts import CameraTelegramAlerts
from app.modules.camera.exceptions import CameraNotRunningError
from app.modules.camera.models.frame import CameraRuntimeStatus
from app.modules.camera.utils.config_loader import CameraStreamConfig


@pytest.fixture
def monitor():
    now = [0.0]
    manager = Mock()
    provider = Mock()
    provider.is_ready = True
    provider._config.chat_id = "test-chat"
    provider.send_text.return_value = SimpleNamespace(ok=True)
    config = CameraStreamConfig(
        alert_grace_seconds=30,
        alert_startup_grace_seconds=30,
        alert_stale_frame_seconds=30,
    )
    alerts = CameraTelegramAlerts(manager, config, provider, clock=lambda: now[0])
    camera = SimpleNamespace(id=7, code="CAM-07", name="Cửa trước", location="Sảnh")
    return alerts, manager, provider, now, camera


@pytest.mark.asyncio
async def test_outage_alert_once_after_grace_then_recovery(monitor):
    alerts, manager, provider, now, camera = monitor
    manager.get_status.return_value = CameraRuntimeStatus(
        camera_id=7, is_running=True, is_connected=False, status="reconnecting"
    )
    await alerts._check_camera(camera)
    now[0] = 29
    await alerts._check_camera(camera)
    provider.send_text.assert_not_called()

    now[0] = 30
    await alerts._check_camera(camera)
    now[0] = 90
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 1
    assert "CAM-07" in provider.send_text.call_args.args[1]

    manager.get_status.return_value = CameraRuntimeStatus(
        camera_id=7,
        is_running=True,
        is_connected=True,
        status="online",
        last_frame_at=datetime.now(timezone.utc),
    )
    await alerts._check_camera(camera)
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 2
    assert "kết nối lại" in provider.send_text.call_args.args[1]


@pytest.mark.asyncio
async def test_failed_delivery_retries_and_stale_frame_alerts(monitor):
    alerts, manager, provider, now, camera = monitor
    manager.get_status.return_value = CameraRuntimeStatus(
        camera_id=7, is_running=True, is_connected=True, status="online"
    )
    provider.send_text.side_effect = [RuntimeError("network"), SimpleNamespace(ok=True)]
    await alerts._check_camera(camera)
    now[0] = 30
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 1
    now[0] = 35
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 1
    now[0] = 90
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 2
    assert "Chưa nhận được hình ảnh" in provider.send_text.call_args.args[1]


@pytest.mark.asyncio
async def test_missing_worker_alerts_and_quick_recovery_stays_silent(monitor):
    alerts, manager, provider, now, camera = monitor
    manager.get_status.side_effect = CameraNotRunningError(7)
    await alerts._check_camera(camera)
    now[0] = 30
    await alerts._check_camera(camera)
    assert "chưa chạy" in provider.send_text.call_args.args[1]

    manager.get_status.side_effect = None
    manager.get_status.return_value = CameraRuntimeStatus(
        camera_id=7,
        is_running=True,
        is_connected=True,
        status="online",
        last_frame_at=datetime.now(timezone.utc),
    )
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 2


@pytest.mark.asyncio
async def test_monitoring_off_clears_alert_state_without_sending(monitor):
    alerts, manager, provider, now, camera = monitor
    manager.get_status.side_effect = CameraNotRunningError(7)
    await alerts._check_camera(camera)
    assert camera.id in alerts._states
    alerts._monitoring_enabled = lambda: False
    await alerts.check_once()
    assert alerts._states == {}
    provider.send_text.assert_not_called()


@pytest.mark.asyncio
async def test_recovery_delivery_waits_and_retries(monitor):
    alerts, manager, provider, now, camera = monitor
    manager.get_status.side_effect = CameraNotRunningError(7)
    await alerts._check_camera(camera)
    now[0] = 30
    await alerts._check_camera(camera)
    manager.get_status.side_effect = None
    manager.get_status.return_value = CameraRuntimeStatus(
        camera_id=7,
        is_running=True,
        is_connected=True,
        status="online",
        last_frame_at=datetime.now(timezone.utc),
    )
    provider.send_text.side_effect = RuntimeError("network")
    await alerts._check_camera(camera)
    assert camera.id in alerts._states
    now[0] = 35
    await alerts._check_camera(camera)
    assert camera.id in alerts._states
    assert provider.send_text.call_count == 2
    provider.send_text.side_effect = None
    now[0] = 90
    await alerts._check_camera(camera)
    assert camera.id not in alerts._states
    assert provider.send_text.call_count == 3


@pytest.mark.asyncio
async def test_first_connection_gets_longer_grace_than_later_outage(monitor):
    alerts, manager, provider, now, camera = monitor
    alerts._config.alert_startup_grace_seconds = 180
    manager.get_status.side_effect = CameraNotRunningError(7)
    await alerts._check_camera(camera)
    now[0] = 30
    await alerts._check_camera(camera)
    provider.send_text.assert_not_called()
    manager.get_status.side_effect = None
    manager.get_status.return_value = CameraRuntimeStatus(
        camera_id=7,
        is_running=True,
        is_connected=True,
        status="online",
        last_frame_at=datetime.now(timezone.utc),
    )
    await alerts._check_camera(camera)
    manager.get_status.side_effect = CameraNotRunningError(7)
    now[0] = 31
    await alerts._check_camera(camera)
    now[0] = 61
    await alerts._check_camera(camera)
    assert provider.send_text.call_count == 1
