"""Tests for Telegram provider send path (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.event.config import TelegramConfig
from app.modules.event.notification.formatter import build_alert_message
from app.modules.event.schemas.records import EventRecord
from app.modules.event.schemas.status import EventStatus
from app.modules.event.telegram.provider import TelegramProvider

from .conftest import make_event


def _record() -> EventRecord:
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
        duration=ev.duration,
        roi=ev.roi,
        status=EventStatus.NEW,
    )


def test_telegram_send_message_success():
    cfg = TelegramConfig(enabled=True, bot_token="tok", chat_id="123", send_snapshot=False, send_video=False)
    provider = TelegramProvider(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True}
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        result = provider.send(build_alert_message(_record()))
    assert result.ok is True
    assert result.skipped is False


def test_telegram_send_network_error_raises():
    cfg = TelegramConfig(enabled=True, bot_token="tok", chat_id="123", send_snapshot=False)
    provider = TelegramProvider(cfg)
    mock_client = MagicMock()
    mock_client.post.side_effect = RuntimeError("network")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("httpx.Client", return_value=mock_client):
        import pytest
        from app.modules.event.exceptions import TelegramError

        with pytest.raises(TelegramError):
            provider.send(build_alert_message(_record()))
