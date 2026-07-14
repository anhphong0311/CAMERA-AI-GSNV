"""
Config loaders cho Event Processing Center.

Nạp event.yaml / snapshot.yaml / recorder.yaml / notification.yaml / telegram.yaml.
Secret Telegram ưu tiên đọc từ ENV (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class EventConfig(BaseModel):
    """Cấu hình chung event pipeline."""

    storage_dir: str = "data/evidence"
    validate_events: bool = True
    process_snapshot: bool = True
    process_video: bool = True
    process_notification: bool = True
    persist_db: bool = False
    history_size: int = Field(default=2000, ge=1)
    notification_workers: int = Field(default=1, ge=1, le=16)


class SnapshotConfig(BaseModel):
    """Cấu hình snapshot."""

    enabled: bool = True
    format: str = "jpg"
    quality: int = Field(default=90, ge=1, le=100)
    dir: str = "data/evidence/snapshots"
    timeout_ms: int = Field(default=200, ge=1)


class RecorderConfig(BaseModel):
    """Cấu hình video recorder."""

    enabled: bool = True
    pre_seconds: float = Field(default=10.0, ge=0.0)
    post_seconds: float = Field(default=10.0, ge=0.0)
    fps: int = Field(default=15, ge=1, le=60)
    codec: str = "mp4v"
    dir: str = "data/evidence/videos"
    ring_buffer_seconds: float = Field(default=30.0, ge=1.0)
    max_export_seconds: float = Field(default=5.0, ge=0.1)


class NotificationConfig(BaseModel):
    """Cấu hình notification queue + dedup + cooldown."""

    enabled: bool = True
    channel: str = "telegram"
    cooldown_seconds: float = Field(default=300.0, ge=0.0)
    dedup_window_seconds: float = Field(default=300.0, ge=0.0)
    queue_max: int = Field(default=1000, ge=1)


class RetryConfig(BaseModel):
    """Cấu hình retry."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff: List[float] = Field(default_factory=lambda: [1.0, 5.0, 10.0])

    def delay_for(self, attempt: int) -> float:
        """Độ trễ (giây) cho lần retry thứ `attempt` (1-based)."""
        if not self.backoff:
            return 0.0
        idx = min(max(attempt - 1, 0), len(self.backoff) - 1)
        return self.backoff[idx]


class TelegramConfig(BaseModel):
    """Cấu hình Telegram service."""

    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    api_base: str = "https://api.telegram.org"
    timeout_seconds: float = Field(default=3.0, ge=0.1)
    send_snapshot: bool = True
    send_video: bool = True
    retry: RetryConfig = Field(default_factory=RetryConfig)

    @property
    def is_ready(self) -> bool:
        """Đã đủ token + chat_id và được bật."""
        return bool(self.enabled and self.bot_token and self.chat_id)


def _find(env: str, filename: str) -> Path:
    """Tìm file config theo env hoặc vị trí mặc định."""
    candidates: List[Path] = []
    env_path = os.getenv(env)
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path(f"/config/{filename}"),
            Path(f"config/{filename}"),
            Path(__file__).resolve().parents[5] / "config" / filename,
            Path(__file__).resolve().parents[4] / "config" / filename,
        ]
    )
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def load_event_config(path: Optional[str] = None) -> EventConfig:
    """Nạp event.yaml."""
    p = Path(path) if path else _find("EVENT_CONFIG_PATH", "event.yaml")
    return EventConfig(**_read_yaml(p))


@lru_cache
def load_snapshot_config(path: Optional[str] = None) -> SnapshotConfig:
    """Nạp snapshot.yaml."""
    p = Path(path) if path else _find("SNAPSHOT_CONFIG_PATH", "snapshot.yaml")
    return SnapshotConfig(**_read_yaml(p))


@lru_cache
def load_recorder_config(path: Optional[str] = None) -> RecorderConfig:
    """Nạp recorder.yaml."""
    p = Path(path) if path else _find("RECORDER_CONFIG_PATH", "recorder.yaml")
    return RecorderConfig(**_read_yaml(p))


@lru_cache
def load_notification_config(path: Optional[str] = None) -> NotificationConfig:
    """Nạp notification.yaml."""
    p = Path(path) if path else _find("NOTIFICATION_CONFIG_PATH", "notification.yaml")
    return NotificationConfig(**_read_yaml(p))


@lru_cache
def load_telegram_config(path: Optional[str] = None) -> TelegramConfig:
    """Nạp telegram.yaml (ENV ghi đè secret)."""
    p = Path(path) if path else _find("TELEGRAM_CONFIG_PATH", "telegram.yaml")
    data = _read_yaml(p)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if token:
        data["bot_token"] = token
        data.setdefault("enabled", True)
    if chat:
        data["chat_id"] = chat
    return TelegramConfig(**data)
