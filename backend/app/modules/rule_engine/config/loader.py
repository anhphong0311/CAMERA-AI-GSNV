"""
Config loaders cho Rule Engine — rule_engine.yaml / severity.yaml / cooldown.yaml.

rules.yaml được nạp bởi rule_parser (danh sách rule).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field


class PerformanceConfig(BaseModel):
    """Cấu hình tính điểm hiệu suất."""

    window_minutes: int = Field(default=60, ge=1, le=1440)
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "phone": 1.0,
            "talking": 0.8,
            "eating": 0.5,
            "sleeping": 1.5,
            "away": 1.0,
            "idle": 0.7,
        }
    )


class RuleEngineConfig(BaseModel):
    """Cấu hình engine tổng."""

    duplicate_window: float = Field(default=300.0, ge=0.0)
    default_cooldown: float = Field(default=300.0, ge=0.0)
    confirmation_frames: int = Field(default=1, ge=1, le=1000)
    low_motion_speed: float = Field(default=2.0, ge=0.0)
    nearby_person_distance: float = Field(default=150.0, ge=0.0)
    temporal_windows: List[int] = Field(
        default_factory=lambda: [10, 30, 60, 300, 600, 1800]
    )
    max_states: int = Field(default=5000, ge=1)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)


class SeverityLevel(BaseModel):
    """Một mức severity."""

    rank: int
    color: str = "#6b7280"


class SeverityConfig(BaseModel):
    """Bảng severity."""

    levels: Dict[str, SeverityLevel] = Field(default_factory=dict)

    def rank(self, name: str) -> int:
        """Rank số của một severity (0 nếu không có)."""
        lvl = self.levels.get(name.upper())
        return lvl.rank if lvl else 0


class CooldownConfig(BaseModel):
    """Cooldown theo rule."""

    default: float = 300.0
    rules: Dict[str, float] = Field(default_factory=dict)

    def for_rule(self, rule_id: str) -> float:
        """Cooldown (giây) cho một rule."""
        return self.rules.get(rule_id, self.default)


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
def load_rule_engine_config(path: str | None = None) -> RuleEngineConfig:
    """Nạp rule_engine.yaml."""
    p = Path(path) if path else _find("RULE_ENGINE_CONFIG_PATH", "rule_engine.yaml")
    return RuleEngineConfig(**_read_yaml(p))


@lru_cache
def load_severity_config(path: str | None = None) -> SeverityConfig:
    """Nạp severity.yaml."""
    p = Path(path) if path else _find("SEVERITY_CONFIG_PATH", "severity.yaml")
    return SeverityConfig(**_read_yaml(p))


@lru_cache
def load_cooldown_config(path: str | None = None) -> CooldownConfig:
    """Nạp cooldown.yaml."""
    p = Path(path) if path else _find("COOLDOWN_CONFIG_PATH", "cooldown.yaml")
    return CooldownConfig(**_read_yaml(p))


def rules_config_path() -> Path:
    """Đường dẫn rules.yaml."""
    return _find("RULES_CONFIG_PATH", "rules.yaml")
