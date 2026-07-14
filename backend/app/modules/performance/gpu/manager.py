"""
GPU Manager & Multi-GPU scheduler (Sprint 10).

Interface quản lý thiết bị CUDA, load balancing camera → GPU.
Không global state — instance inject qua PerformanceContainer.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from app.modules.performance.config.loader import GpuConfig


@dataclass
class GpuDeviceInfo:
    index: int
    name: str = "unknown"
    total_vram_mb: float = 0.0
    used_vram_mb: float = 0.0
    utilization: float = 0.0
    temperature_c: Optional[float] = None
    assigned_cameras: List[int] = field(default_factory=list)


class GpuManager:
    """Phát hiện GPU, gán camera, theo dõi VRAM/utilization."""

    def __init__(self, config: GpuConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._devices: List[GpuDeviceInfo] = []
        self._rr_index = 0
        self._loads: Dict[int, int] = {}
        self._discover()

    def _discover(self) -> None:
        self._devices.clear()
        if not self._config.enabled:
            self._devices.append(GpuDeviceInfo(index=-1, name="cpu"))
            return
        try:
            import pynvml  # type: ignore

            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            indices = self._config.devices or list(range(count))
            for idx in indices:
                if idx >= count:
                    continue
                handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode()
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temp = None
                try:
                    temp = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
                except Exception:
                    pass
                self._devices.append(
                    GpuDeviceInfo(
                        index=idx,
                        name=str(name),
                        total_vram_mb=mem.total / 1024 / 1024,
                        used_vram_mb=mem.used / 1024 / 1024,
                        utilization=float(util.gpu),
                        temperature_c=temp,
                    )
                )
            pynvml.nvmlShutdown()
        except Exception as exc:
            logger.debug("GPU discovery fallback CPU: {}", exc)
            self._devices.append(GpuDeviceInfo(index=-1, name="cpu"))

    def refresh(self) -> None:
        """Cập nhật metrics GPU."""
        self._discover()

    def assign_camera(self, camera_id: int) -> str:
        """Gán camera → device string (cuda:N hoặc cpu)."""
        with self._lock:
            if not self._devices or self._devices[0].index < 0:
                return "cpu"
            if self._config.load_balance == "least_loaded":
                idx = min(self._loads.keys() or [0], key=lambda k: self._loads.get(k, 0))
            else:
                idx = self._devices[self._rr_index % len(self._devices)].index
                self._rr_index += 1
            self._loads[idx] = self._loads.get(idx, 0) + 1
            for d in self._devices:
                if d.index == idx and camera_id not in d.assigned_cameras:
                    d.assigned_cameras.append(camera_id)
            return f"cuda:{idx}" if idx >= 0 else "cpu"

    def release_camera(self, camera_id: int) -> None:
        with self._lock:
            for d in self._devices:
                if camera_id in d.assigned_cameras:
                    d.assigned_cameras.remove(camera_id)

    def snapshot(self) -> List[dict]:
        self.refresh()
        with self._lock:
            return [
                {
                    "index": d.index,
                    "name": d.name,
                    "total_vram_mb": round(d.total_vram_mb, 1),
                    "used_vram_mb": round(d.used_vram_mb, 1),
                    "vram_percent": round(d.used_vram_mb / d.total_vram_mb * 100, 1) if d.total_vram_mb else 0,
                    "utilization": d.utilization,
                    "temperature_c": d.temperature_c,
                    "assigned_cameras": list(d.assigned_cameras),
                    "cuda_streams": self._config.cuda_streams,
                    "pinned_memory": self._config.pinned_memory,
                }
                for d in self._devices
            ]
