"""Load performance.yaml — cấu hình tối ưu Sprint 10."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Literal

import yaml
from pydantic import BaseModel, Field


class BackendConfig(BaseModel):
    type: Literal["pytorch", "onnx", "tensorrt"] = "pytorch"
    onnx_path: str = "models/yolo11n.onnx"
    tensorrt_path: str = "models/yolo11n.engine"
    precision: Literal["fp32", "fp16", "int8"] = "fp32"
    auto_export_onnx: bool = False


class FrameSchedulerConfig(BaseModel):
    enabled: bool = True
    target_ai_fps: float = Field(default=10.0, ge=1.0, le=120.0)
    max_capture_fps: float = Field(default=30.0, ge=1.0, le=120.0)
    skip_mode: Literal["adaptive", "fixed", "priority"] = "adaptive"
    priority_cameras: List[int] = Field(default_factory=list)


class WorkerPoolConfig(BaseModel):
    detection_workers: int = Field(default=2, ge=1, le=64)
    tracking_workers: int = Field(default=1, ge=1, le=32)
    behavior_workers: int = Field(default=1, ge=1, le=32)
    rule_workers: int = Field(default=1, ge=1, le=32)
    event_workers: int = Field(default=1, ge=1, le=32)
    notification_workers: int = Field(default=1, ge=1, le=32)
    max_queue_depth: int = Field(default=32, ge=4, le=512)


class MemoryConfig(BaseModel):
    frame_pool_size: int = Field(default=64, ge=8, le=1024)
    buffer_pool_size: int = Field(default=32, ge=4, le=512)
    ring_buffer_seconds: int = Field(default=30, ge=5, le=300)


class GpuConfig(BaseModel):
    enabled: bool = True
    cuda_streams: int = Field(default=2, ge=1, le=8)
    pinned_memory: bool = True
    load_balance: Literal["round_robin", "least_loaded"] = "round_robin"
    devices: List[int] = Field(default_factory=list)


class QueueOptConfig(BaseModel):
    use_priority: bool = True
    redis_backed: bool = False
    drop_policy: Literal["oldest", "newest"] = "oldest"


class CacheConfig(BaseModel):
    enabled: bool = True
    ttl_seconds: int = Field(default=300, ge=30, le=86400)
    prefixes: Dict[str, str] = Field(default_factory=dict)


class DatabaseOptConfig(BaseModel):
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=200)
    pool_pre_ping: bool = True
    statement_cache_size: int = Field(default=100, ge=0, le=1000)


class NetworkConfig(BaseModel):
    rtsp_buffer_size: int = Field(default=1, ge=1, le=10)
    reconnect_max_delay_s: int = Field(default=60, ge=5, le=600)
    heartbeat_interval_s: int = Field(default=10, ge=1, le=120)
    bandwidth_monitor: bool = True


class PipelineConfig(BaseModel):
    enabled: bool = True
    poll_interval_ms: int = Field(default=10, ge=1, le=1000)
    chain_tracking: bool = False
    chain_behavior: bool = False
    chain_rules: bool = False


class BenchmarkConfig(BaseModel):
    runs: int = Field(default=50, ge=5, le=500)
    warmup: int = Field(default=5, ge=0, le=50)
    backends: List[str] = Field(default_factory=lambda: ["pytorch", "onnx", "tensorrt"])


class StressConfig(BaseModel):
    durations_s: int = Field(default=5, ge=1, le=120)
    camera_counts: List[int] = Field(default_factory=lambda: [1, 5, 10, 20, 50, 100])


class PerformanceConfig(BaseModel):
    backend: BackendConfig = Field(default_factory=BackendConfig)
    frame_scheduler: FrameSchedulerConfig = Field(default_factory=FrameSchedulerConfig)
    worker_pool: WorkerPoolConfig = Field(default_factory=WorkerPoolConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    gpu: GpuConfig = Field(default_factory=GpuConfig)
    queue: QueueOptConfig = Field(default_factory=QueueOptConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    database: DatabaseOptConfig = Field(default_factory=DatabaseOptConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    stress: StressConfig = Field(default_factory=StressConfig)
    targets: Dict[str, Dict[str, Dict[int, int]]] = Field(default_factory=dict)


def _default_path() -> Path:
    env = os.getenv("PERFORMANCE_CONFIG_PATH")
    if env:
        return Path(env)
    for p in (
        Path("/config/performance.yaml"),
        Path("config/performance.yaml"),
        Path(__file__).resolve().parents[5] / "config" / "performance.yaml",
        Path(__file__).resolve().parents[4] / "config" / "performance.yaml",
    ):
        if p.exists():
            return p
    return Path("config/performance.yaml")


@lru_cache
def load_performance_config(path: str | None = None) -> PerformanceConfig:
    config_path = Path(path) if path else _default_path()
    if not config_path.exists():
        return PerformanceConfig()
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return PerformanceConfig(**raw)
