"""
Thu thập system metrics (CPU / RAM / Disk / Network / GPU / VRAM).

psutil bắt buộc (đã có). GPU/VRAM dùng pynvml nếu khả dụng, ngược lại trả None.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

_last_net: Optional[tuple[float, float, float]] = None  # (ts, bytes_sent, bytes_recv)


def _gpu_metrics() -> Dict[str, Any]:
    """GPU/VRAM qua pynvml (tùy chọn)."""
    try:
        import pynvml  # type: ignore

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        return {
            "gpu_percent": float(util.gpu),
            "vram_used_mb": round(mem.used / 1024 / 1024, 1),
            "vram_total_mb": round(mem.total / 1024 / 1024, 1),
            "vram_percent": round(mem.used / mem.total * 100, 1),
            "gpu_available": True,
        }
    except Exception:
        return {
            "gpu_percent": None,
            "vram_used_mb": None,
            "vram_total_mb": None,
            "vram_percent": None,
            "gpu_available": False,
        }


def collect_system_metrics() -> Dict[str, Any]:
    """Trả về snapshot metrics hệ thống."""
    global _last_net
    try:
        import psutil  # type: ignore
    except ImportError:
        return {"cpu_percent": None, "gpu_available": False}

    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    net = psutil.net_io_counters()
    now = time.time()
    net_sent_kbps = net_recv_kbps = 0.0
    if _last_net is not None:
        dt = max(now - _last_net[0], 1e-3)
        net_sent_kbps = round((net.bytes_sent - _last_net[1]) / dt / 1024, 1)
        net_recv_kbps = round((net.bytes_recv - _last_net[2]) / dt / 1024, 1)
    _last_net = (now, net.bytes_sent, net.bytes_recv)

    data: Dict[str, Any] = {
        "cpu_percent": round(cpu, 1),
        "ram_percent": round(mem.percent, 1),
        "ram_used_mb": round(mem.used / 1024 / 1024, 1),
        "ram_total_mb": round(mem.total / 1024 / 1024, 1),
        "disk_percent": round(disk.percent, 1),
        "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
        "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
        "net_sent_kbps": net_sent_kbps,
        "net_recv_kbps": net_recv_kbps,
    }
    data.update(_gpu_metrics())
    return data
