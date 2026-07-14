"""
Unit test — BenchmarkService (synthetic pose, không cần model thật).
"""

from __future__ import annotations

from app.modules.behavior.config import BehaviorConfig
from app.modules.behavior.services import BenchmarkService


def test_benchmark_runs_synthetic():
    svc = BenchmarkService(BehaviorConfig())
    result = svc.run(frames=5, people=3, width=640, height=480)
    assert result.frames == 5
    assert result.people == 3
    assert result.used_real_pose is False
    assert result.fps > 0
    assert result.avg_latency_ms >= 0


def test_benchmark_20_people():
    svc = BenchmarkService(BehaviorConfig())
    result = svc.run(frames=3, people=20, width=1280, height=720)
    assert result.people == 20
    d = result.to_dict()
    assert d["frames"] == 3
