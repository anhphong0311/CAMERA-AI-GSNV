"""Test Telegram provider (skipped khi chưa cấu hình) + formatter + bot commands."""

from __future__ import annotations

from app.modules.event.config import TelegramConfig
from app.modules.event.notification.formatter import build_alert_message
from app.modules.event.schemas.records import EventRecord
from app.modules.event.schemas.status import EventStatus
from app.modules.event.telegram import COMMANDS, TelegramProvider

from .conftest import BASE_TIME, build_service, frame, make_event


def _record() -> EventRecord:
    from datetime import timedelta

    ev = make_event()
    return EventRecord(
        event_id=ev.event_id,
        camera_id=ev.camera_id,
        camera_name=ev.camera_name,
        track_id=ev.track_id,
        rule_id=ev.rule_id,
        event_type=ev.event_type,
        severity=ev.severity,
        confidence=ev.confidence,
        start_time=ev.start_time,
        end_time=ev.start_time + timedelta(seconds=ev.duration),
        duration=ev.duration,
        roi=ev.roi,
        status=EventStatus.NEW,
    )


def test_formatter_alert_message():
    msg = build_alert_message(_record())
    assert "🚨 AI Employee Monitoring" in msg.body
    assert "📷 Camera : Office01" in msg.body
    assert "👤 Track ID : 12" in msg.body
    assert "Sử dụng điện thoại" in msg.body
    assert "📱 Từ :" in msg.body
    assert "📱 Đến :" in msg.body
    assert "18 giây" in msg.body
    assert "📷 Snapshot" in msg.body
    assert "📹 Video Evidence" in msg.body


def test_formatter_away_from_desk_range():
    from datetime import timedelta

    ev = make_event(rule_id="AWAY_FROM_DESK", duration=303.0)
    record = EventRecord(
        event_id=ev.event_id,
        camera_id=ev.camera_id,
        camera_name="CAM02",
        track_id=195,
        rule_id="AWAY_FROM_DESK",
        event_type="AWAY_FROM_DESK",
        severity="MEDIUM",
        confidence=0.9,
        start_time=BASE_TIME,
        end_time=BASE_TIME + timedelta(seconds=303),
        duration=303.0,
        status=EventStatus.NEW,
    )
    msg = build_alert_message(record)
    assert "Rời khỏi vị trí làm việc" in msg.body
    # BASE_TIME UTC 09:15:22 → VN (UTC+7) 16:15:22
    assert "🚪 Rời lúc : 16:15:22" in msg.body
    assert "KHÔNG có nhân viên" in msg.body
    assert "303 giây" in msg.body
    assert "bàn làm việc không có nhân viên" in msg.body


def test_formatter_phone_usage_range():
    from datetime import timedelta

    ev = make_event(rule_id="PHONE_USAGE", duration=215.0)
    record = EventRecord(
        event_id=ev.event_id,
        camera_id=ev.camera_id,
        camera_name="CAM01",
        track_id=12,
        rule_id="PHONE_USAGE",
        event_type="PHONE_USAGE",
        severity="HIGH",
        confidence=0.96,
        start_time=BASE_TIME,
        end_time=BASE_TIME + timedelta(seconds=215),
        duration=215.0,
        status=EventStatus.NEW,
    )
    msg = build_alert_message(record)
    assert "Sử dụng điện thoại" in msg.body
    assert "📱 Từ : 16:15:22" in msg.body
    assert "📱 Đến : 16:18:57" in msg.body
    assert "215 giây" in msg.body
    assert "nhân viên đang sử dụng điện thoại" in msg.body


def test_telegram_provider_not_ready_skips():
    provider = TelegramProvider(TelegramConfig())  # chưa cấu hình
    assert not provider.is_ready
    result = provider.send(build_alert_message(_record()))
    assert result.skipped is True
    assert result.ok is False


def test_bot_commands(tmp_path):
    import asyncio

    service, _ = build_service(tmp_path)
    service.push_frame(1, frame())
    service.ingest_now(make_event())
    assert "/bat" in COMMANDS and "/tat" in COMMANDS
    assert "/system_on" in COMMANDS and "/system_off" in COMMANDS

    async def _run():
        assert "AEMS" in await service.handle_command("/help")
        assert "Event Center" in await service.handle_command("/status")
        cams = await service.handle_command("/cameras")
        assert "Camera" in cams or "#1" in cams
        assert "PHONE_USAGE" in await service.handle_command("/events")
        assert "PHONE_USAGE" in await service.handle_command("/latest")
        assert "không hợp lệ" in await service.handle_command("/unknown")
        # Chưa bind system control
        assert "Chưa gắn" in await service.handle_command("/bat")
        assert "Chưa gắn" in await service.handle_command("/tat")

    asyncio.run(_run())


def test_system_on_off_commands(tmp_path):
    import asyncio
    from types import SimpleNamespace

    from app.modules.system.control import SystemControlService

    service, _ = build_service(tmp_path)
    state_file = tmp_path / "system_state.json"

    class FakeManager:
        def __init__(self):
            self.stopped = False
            self.started_ids = []

        def list_running_ids(self):
            return [] if self.stopped else [1, 2]

        def stop_all(self):
            self.stopped = True

    class FakeAI:
        def __init__(self):
            self.running = True

        def stop_pipeline(self):
            self.running = False

        def start_pipeline(self):
            self.running = True

        def get_statistics(self):
            return {"pipeline_running": self.running}

    class FakeOrch:
        def __init__(self):
            self._running = True

        async def stop(self):
            self._running = False

        async def start(self):
            self._running = True

    app = SimpleNamespace(
        state=SimpleNamespace(
            camera_manager=FakeManager(),
            ai_service=FakeAI(),
            performance=SimpleNamespace(orchestrator=FakeOrch()),
            camera_config=None,
        )
    )

    control = SystemControlService(app, state_path=state_file)
    service.bind_system_control(control)

    async def _run():
        off = await service.handle_command("/tat")
        assert "TẮT" in off
        assert control.is_monitoring is False
        assert app.state.ai_service.running is False
        assert app.state.performance.orchestrator._running is False
        assert state_file.exists()

        already = await service.handle_command("/system_off")
        assert "đã tắt sẵn" in already.lower() or "ĐANG TẮT" in already or "tắt sẵn" in already

        # Turn on without DB cameras — expect camera bootstrap error or success message
        on = await service.handle_command("/bat")
        assert "BẬT" in on or "lỗi" in on.lower() or "⚠️" in on
        # monitoring flag should be True after turn_on attempt
        assert control.is_monitoring is True
        assert app.state.ai_service.running is True

        st = await service.handle_command("/system_status")
        assert "Hệ thống giám sát" in st

        again = await service.handle_command("/bat")
        assert "Đường link xem" in again
        assert "http://localhost:8080/live" in again

    asyncio.run(_run())
