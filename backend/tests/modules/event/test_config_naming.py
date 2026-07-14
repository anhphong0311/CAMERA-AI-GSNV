"""Test config loaders + naming util."""

from __future__ import annotations

from datetime import datetime

from app.modules.event.config import (
    EventConfig,
    RetryConfig,
    TelegramConfig,
    load_event_config,
    load_recorder_config,
    load_telegram_config,
)
from app.modules.event.utils.naming import build_evidence_name, camera_label, sanitize


def test_load_configs_defaults():
    cfg = load_event_config()
    assert isinstance(cfg, EventConfig)
    rec = load_recorder_config()
    assert rec.pre_seconds >= 0 and rec.post_seconds >= 0
    tg = load_telegram_config()
    assert isinstance(tg, TelegramConfig)


def test_retry_backoff_delays():
    rc = RetryConfig(max_attempts=3, backoff=[1, 5, 10])
    assert rc.delay_for(1) == 1
    assert rc.delay_for(2) == 5
    assert rc.delay_for(3) == 10
    assert rc.delay_for(9) == 10  # clamp


def test_telegram_ready_flag():
    assert not TelegramConfig().is_ready
    assert TelegramConfig(enabled=True, bot_token="t", chat_id="c").is_ready


def test_sanitize_and_camera_label():
    assert sanitize("Office 01") == "Office01"
    assert camera_label(1, "Office 01") == "Office01"
    assert camera_label(3, None) == "CAM03"


def test_build_evidence_name():
    ts = datetime(2026, 7, 5, 9, 15, 22)
    name = build_evidence_name(1, "Office01", 12, "PHONE_USAGE", ts, "jpg")
    assert name == "Office01_TRACK12_PHONE_USAGE_20260705_091522.jpg"
    vid = build_evidence_name(1, "Office01", 12, "PHONE", ts, "mp4")
    assert vid.endswith("_20260705_091522.mp4")
