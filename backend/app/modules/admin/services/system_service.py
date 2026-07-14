"""
System Monitor Service (Sprint 9).

CPU / GPU / VRAM / RAM / Disk / Temperature / Network / Camera Health / Inference FPS /
Queue Size. Tái sử dụng bộ thu metrics hệ thống; các chỉ số nghiệp vụ (camera health,
fps, queue) nạp qua provider callable để giữ tính độc lập module.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

MetricProvider = Callable[[], Dict[str, Any]]


def _temperature() -> Optional[float]:
    try:
        import psutil  # type: ignore

        if not hasattr(psutil, "sensors_temperatures"):
            return None
        temps = psutil.sensors_temperatures()
        for readings in temps.values():
            if readings:
                return round(float(readings[0].current), 1)
        return None
    except Exception:
        return None


class SystemMonitorService:
    def __init__(self, providers: Optional[Dict[str, MetricProvider]] = None) -> None:
        self._providers = providers or {}

    def register_provider(self, name: str, provider: MetricProvider) -> None:
        self._providers[name] = provider

    def snapshot(self) -> Dict[str, Any]:
        from app.modules.realtime.metrics import collect_system_metrics

        data = collect_system_metrics()
        data["temperature_c"] = _temperature()
        for name, provider in self._providers.items():
            try:
                data[name] = provider()
            except Exception:  # noqa: BLE001
                data[name] = None
        data.setdefault("camera_health", None)
        data.setdefault("inference_fps", None)
        data.setdefault("queue_size", None)
        return data
