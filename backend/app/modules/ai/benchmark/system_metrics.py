"""
System metrics — đo CPU/RAM/GPU/VRAM cho benchmark.

Lazy import psutil/torch để module import an toàn khi thiếu dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemMetrics:
    """Ảnh chụp tài nguyên hệ thống."""

    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    gpu_percent: Optional[float] = None
    vram_mb: Optional[float] = None


def read_cpu_memory() -> tuple[Optional[float], Optional[float]]:
    """
    Đọc %CPU và RAM tiến trình (MB).

    Returns:
        Tuple (cpu_percent, memory_mb) — None nếu psutil không có.
    """
    try:
        import psutil

        process = psutil.Process()
        cpu = psutil.cpu_percent(interval=None)
        mem_mb = process.memory_info().rss / (1024 * 1024)
        return cpu, mem_mb
    except Exception:
        return None, None


def read_gpu_metrics() -> tuple[Optional[float], Optional[float]]:
    """
    Đọc %GPU util và VRAM (MB) qua torch.cuda nếu có.

    torch không cung cấp % utilization trực tiếp; trả về mem allocated làm
    proxy VRAM. gpu_percent để None nếu không đo được.

    Returns:
        Tuple (gpu_percent, vram_mb).
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return None, None
        vram_mb = torch.cuda.memory_allocated() / (1024 * 1024)
        gpu_percent: Optional[float] = None
        try:
            # torch >= 2.x có thể cung cấp utilization qua nvml
            gpu_percent = float(torch.cuda.utilization())  # type: ignore[attr-defined]
        except Exception:
            gpu_percent = None
        return gpu_percent, vram_mb
    except Exception:
        return None, None


def snapshot() -> SystemMetrics:
    """Chụp toàn bộ metrics hiện tại."""
    cpu, mem = read_cpu_memory()
    gpu, vram = read_gpu_metrics()
    return SystemMetrics(
        cpu_percent=cpu, memory_mb=mem, gpu_percent=gpu, vram_mb=vram
    )
