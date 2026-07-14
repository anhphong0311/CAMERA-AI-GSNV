"""Load evidence.yaml configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class FrameBufferSettings(BaseModel):
    seconds: float = Field(default=30.0, ge=5.0, le=60.0)
    fps: int = Field(default=15, ge=1, le=60)


class PhoneTimerSettings(BaseModel):
    confirm_seconds: float = Field(default=10.0, ge=1.0)
    gap_reset_seconds: float = Field(default=2.0, ge=0.0)


class LeaveEventSettings(BaseModel):
    confirm_seconds: float = Field(default=300.0, ge=1.0)
    cancel_return_seconds: float = Field(default=300.0, ge=1.0)


class VideoEvidenceSettings(BaseModel):
    pre_seconds: float = Field(default=10.0, ge=0.0)
    post_seconds: float = Field(default=10.0, ge=0.0)
    max_wait_seconds: float = Field(default=15.0, ge=1.0)


class SnapshotSettings(BaseModel):
    use_evidence_time: bool = True


class EvidenceConfig(BaseModel):
    frame_buffer: FrameBufferSettings = Field(default_factory=FrameBufferSettings)
    phone: PhoneTimerSettings = Field(default_factory=PhoneTimerSettings)
    leave: LeaveEventSettings = Field(default_factory=LeaveEventSettings)
    video: VideoEvidenceSettings = Field(default_factory=VideoEvidenceSettings)
    snapshot: SnapshotSettings = Field(default_factory=SnapshotSettings)

    def gap_reset_for_rule(self, rule_id: str) -> Optional[float]:
        """Gap reset (giây) cho rule có timer — None nếu reset ngay."""
        if rule_id == "PHONE_USAGE":
            return self.phone.gap_reset_seconds
        return None

    def evidence_time_for_leave(self) -> bool:
        return True


def _find(env: str, filename: str) -> Path:
    candidates: List[Path] = []
    env_path = os.getenv(env)
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path(f"/config/{filename}"),
            Path("config/{filename}"),
            Path(__file__).resolve().parents[5] / "config" / filename,
            Path(__file__).resolve().parents[4] / "config" / filename,
        ]
    )
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


@lru_cache
def load_evidence_config(path: Optional[str] = None) -> EvidenceConfig:
    p = Path(path) if path else _find("EVIDENCE_CONFIG_PATH", "evidence.yaml")
    if not p.exists():
        return EvidenceConfig()
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return EvidenceConfig(**data)
