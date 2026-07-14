"""
Performance Monitor (Sprint 10) — thu thập metrics toàn hệ thống.

CPU/GPU/VRAM/FPS/Queue/Delay/Workers — không global state.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from app.modules.realtime.metrics import collect_system_metrics


class PerformanceCollector:
    """Gom metrics từ các provider inject."""

    def __init__(self) -> None:
        self._providers: Dict[str, Callable[[], Any]] = {}
        self._history: List[dict] = []
        self._history_max = 120

    def register(self, name: str, provider: Callable[[], Any]) -> None:
        self._providers[name] = provider

    def snapshot(self) -> dict:
        data = collect_system_metrics()
        data["timestamp"] = time.time()
        data["temperature_c"] = data.get("temperature_c")
        for name, provider in self._providers.items():
            try:
                data[name] = provider()
            except Exception:
                data[name] = None
        self._history.append(data)
        if len(self._history) > self._history_max:
            self._history = self._history[-self._history_max :]
        return data

    def performance_report(self) -> dict:
        snap = self.snapshot()
        return {
            "cpu_percent": snap.get("cpu_percent"),
            "gpu_percent": snap.get("gpu_percent"),
            "vram_percent": snap.get("vram_percent"),
            "ram_percent": snap.get("ram_percent"),
            "inference_fps": snap.get("inference_fps"),
            "queue_size": snap.get("queue_size"),
            "frame_delay_ms": snap.get("frame_delay_ms"),
            "inference_delay_ms": snap.get("inference_delay_ms"),
            "workers": snap.get("workers"),
            "pipeline": snap.get("pipeline"),
        }

    def history(self, limit: int = 60) -> List[dict]:
        return self._history[-limit:]
