"""Unit test — Stress test service."""

from __future__ import annotations

from app.modules.performance.benchmark.stress import StressTestService
from app.modules.performance.config.loader import StressConfig


def test_stress_single_camera():
    svc = StressTestService(StressConfig(durations_s=1, camera_counts=[1]))
    submitted = []

    def submit(cam_id, frame, fid):
        submitted.append((cam_id, fid))

    result = svc.run(submit, camera_counts=[1], duration_s=1)
    assert result["scenarios"][0]["cameras"] == 1
    assert result["scenarios"][0]["submitted"] > 0
    assert result["summary"]["max_cameras_tested"] == 1


def test_stress_multi_camera():
    svc = StressTestService(StressConfig(durations_s=1, camera_counts=[1, 3]))
    result = svc.run(lambda *a: None, camera_counts=[1, 3], duration_s=1)
    assert len(result["scenarios"]) == 2
