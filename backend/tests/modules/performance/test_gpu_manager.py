"""Unit test — GPU Manager."""

from __future__ import annotations

from app.modules.performance.config.loader import GpuConfig
from app.modules.performance.gpu.manager import GpuManager


def test_gpu_manager_cpu_fallback():
    mgr = GpuManager(GpuConfig(enabled=False))
    snap = mgr.snapshot()
    assert len(snap) >= 1
    assert snap[0]["index"] == -1


def test_assign_camera_returns_device():
    mgr = GpuManager(GpuConfig(enabled=False))
    dev = mgr.assign_camera(1)
    assert dev == "cpu"
