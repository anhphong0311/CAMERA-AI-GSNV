"""Pydantic request schemas cho Event API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class RetryRequest(BaseModel):
    """Yêu cầu retry xử lý/gửi lại notification cho một event."""

    event_id: str


class ResendRequest(BaseModel):
    """Yêu cầu gửi lại notification (bỏ qua dedup/cooldown)."""

    event_id: str
    force: bool = True


class IngestEventRequest(BaseModel):
    """Nạp một BehaviorEvent thủ công (test/tích hợp ngoài)."""

    camera_id: int
    track_id: int
    rule_id: str
    event_type: Optional[str] = None
    severity: str = "INFO"
    confidence: float = 0.0
    duration: float = 0.0
    camera_name: Optional[str] = None
    roi: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
