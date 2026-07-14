"""
Pydantic schemas cho Rule Engine API.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field


class RuleCreateRequest(BaseModel):
    """Payload tạo rule mới (JSON). `conditions` là list hoặc group dict."""

    id: str
    name: Optional[str] = None
    description: str = ""
    enabled: bool = True
    severity: str = "INFO"
    priority: int = 3
    cooldown: Optional[float] = None
    actions: List[str] = Field(default_factory=lambda: ["alert"])
    conditions: Union[list, dict]


class RuleUpdateRequest(BaseModel):
    """Payload cập nhật rule (id lấy từ path)."""

    name: Optional[str] = None
    description: str = ""
    enabled: bool = True
    severity: str = "INFO"
    priority: int = 3
    cooldown: Optional[float] = None
    actions: List[str] = Field(default_factory=lambda: ["alert"])
    conditions: Union[list, dict]


class RuleToggleRequest(BaseModel):
    """Payload bật/tắt rule."""

    rule_id: str


def to_rule_dict(body: Any) -> dict:
    """Chuyển request schema → dict cho parser."""
    return body.model_dump(exclude_none=False)
