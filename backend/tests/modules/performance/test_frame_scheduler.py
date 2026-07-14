"""Unit test — Frame Scheduler."""

from __future__ import annotations

from app.modules.performance.config.loader import FrameSchedulerConfig
from app.modules.performance.scheduler.frame_scheduler import FrameScheduler


def test_fixed_skip_ratio():
    cfg = FrameSchedulerConfig(enabled=True, target_ai_fps=10, max_capture_fps=30, skip_mode="fixed")
    sched = FrameScheduler(cfg)
    results = [sched.should_process(1) for _ in range(9)]
    assert sum(results) == 3  # 9 frames, skip 2 of 3


def test_disabled_processes_all():
    cfg = FrameSchedulerConfig(enabled=False)
    sched = FrameScheduler(cfg)
    assert all(sched.should_process(1) for _ in range(5))


def test_priority_camera_always_processed():
    cfg = FrameSchedulerConfig(enabled=True, target_ai_fps=1, skip_mode="adaptive", priority_cameras=[99])
    sched = FrameScheduler(cfg)
    assert sched.should_process(99)
    assert sched.should_process(99)


def test_adaptive_respects_interval():
    cfg = FrameSchedulerConfig(enabled=True, target_ai_fps=100, skip_mode="adaptive")
    sched = FrameScheduler(cfg)
    assert sched.should_process(1)
    # frame liên tiếp trong cùng interval bị skip
    assert not sched.should_process(1)


def test_summary_stats():
    cfg = FrameSchedulerConfig(enabled=True, skip_mode="fixed", target_ai_fps=10, max_capture_fps=30)
    sched = FrameScheduler(cfg)
    for _ in range(6):
        sched.should_process(1)
    summary = sched.summary()
    assert summary["total_processed"] >= 1
    assert "cameras" in summary
