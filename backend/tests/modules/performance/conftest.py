"""Fixtures test Performance module (Sprint 10)."""

from __future__ import annotations

import pytest

from app.modules.performance.config.loader import FrameSchedulerConfig, PerformanceConfig
from app.modules.performance.scheduler.frame_scheduler import FrameScheduler


@pytest.fixture
def frame_scheduler() -> FrameScheduler:
    cfg = FrameSchedulerConfig(enabled=True, target_ai_fps=10, max_capture_fps=30, skip_mode="fixed")
    return FrameScheduler(cfg)


@pytest.fixture
def perf_config() -> PerformanceConfig:
    return PerformanceConfig()
