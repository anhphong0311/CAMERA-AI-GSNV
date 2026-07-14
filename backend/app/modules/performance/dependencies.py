"""
Performance module DI & lifecycle (Sprint 10).

Khởi tạo frame scheduler, GPU manager, pools, worker registry, pipeline orchestrator,
cache, monitor, benchmark — wire vào app.state.performance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Request
from loguru import logger

from app.modules.performance.benchmark.compare import CompareBenchmarkService
from app.modules.performance.benchmark.stress import StressTestService
from app.modules.performance.cache.redis_cache import RedisCache
from app.modules.performance.config import load_performance_config
from app.modules.performance.gpu.manager import GpuManager
from app.modules.performance.monitor.collector import PerformanceCollector
from app.modules.performance.pipeline.orchestrator import PipelineOrchestrator
from app.modules.performance.pool.memory_pool import BufferPool, FramePool
from app.modules.performance.pool.worker_pool import WorkerPool, WorkerPoolRegistry
from app.modules.performance.scheduler.frame_scheduler import FrameScheduler


@dataclass
class PerformanceContainer:
    config: object
    frame_scheduler: FrameScheduler
    gpu_manager: GpuManager
    frame_pool: FramePool
    buffer_pool: BufferPool
    worker_registry: WorkerPoolRegistry
    orchestrator: PipelineOrchestrator
    cache: RedisCache
    collector: PerformanceCollector
    compare_benchmark: CompareBenchmarkService
    stress_test: StressTestService


_perf: Optional[PerformanceContainer] = None


def _noop_handler(_task) -> None:
    pass


async def init_performance_module(app) -> PerformanceContainer:
    """Khởi tạo module performance sau AI + Camera."""
    global _perf
    perf_cfg = load_performance_config()
    det_cfg = getattr(app.state, "ai_config", None)

    # FP16 theo precision config
    if det_cfg and perf_cfg.backend.precision == "fp16":
        det_cfg.half_precision = True

    # Reload AI model với backend đã chọn (nếu khác pytorch)
    ai_service = getattr(app.state, "ai_service", None)
    if ai_service and perf_cfg.backend.type != "pytorch":
        loader = ai_service.loader
        loader._backend_type = perf_cfg.backend.type
        loader._onnx_path = perf_cfg.backend.onnx_path
        loader._tensorrt_path = perf_cfg.backend.tensorrt_path
        loader._auto_export_onnx = perf_cfg.backend.auto_export_onnx
        if loader.is_loaded:
            try:
                ai_service.reload_model()
                logger.info("AI model reloaded with backend={}", perf_cfg.backend.type)
            except Exception as exc:
                logger.warning("Backend {} reload skipped: {}", perf_cfg.backend.type, exc)

    frame_sched = FrameScheduler(perf_cfg.frame_scheduler)
    gpu_mgr = GpuManager(perf_cfg.gpu)
    frame_pool = FramePool(perf_cfg.memory.frame_pool_size)
    buffer_pool = BufferPool(perf_cfg.memory.buffer_pool_size)
    registry = WorkerPoolRegistry()

    wp = perf_cfg.worker_pool
    for name, count in [
        ("detection", wp.detection_workers),
        ("tracking", wp.tracking_workers),
        ("behavior", wp.behavior_workers),
        ("rule", wp.rule_workers),
        ("event", wp.event_workers),
        ("notification", wp.notification_workers),
    ]:
        pool = WorkerPool(name, count, _noop_handler, max_queue=wp.max_queue_depth)
        registry.register(pool)

    def _cam_mgr():
        return getattr(app.state, "camera_manager", None)

    def _ai_svc():
        return getattr(app.state, "ai_service", None)

    orchestrator = PipelineOrchestrator(
        frame_sched, perf_cfg.pipeline,
        get_camera_manager=_cam_mgr,
        get_ai_service=_ai_svc,
        worker_registry=registry,
    )

    cache = RedisCache(perf_cfg.cache)
    await cache.connect()

    collector = PerformanceCollector()
    collector.register("gpu_devices", lambda: gpu_mgr.snapshot())
    collector.register("frame_scheduler", lambda: frame_sched.summary())
    collector.register("frame_pool", lambda: frame_pool.stats())
    collector.register("workers", lambda: registry.all_stats())
    collector.register("pipeline", lambda: orchestrator.stats())
    if ai_service:
        collector.register("inference_fps", lambda: ai_service.get_statistics().get("avg_fps"))
        collector.register("queue_size", lambda: ai_service.pipeline.processed_count)
        collector.register(
            "inference_delay_ms",
            lambda: ai_service.get_statistics().get("avg_inference_ms"),
        )

    compare = CompareBenchmarkService(perf_cfg, det_cfg) if det_cfg else None
    stress = StressTestService(perf_cfg.stress)

    container = PerformanceContainer(
        config=perf_cfg,
        frame_scheduler=frame_sched,
        gpu_manager=gpu_mgr,
        frame_pool=frame_pool,
        buffer_pool=buffer_pool,
        worker_registry=registry,
        orchestrator=orchestrator,
        cache=cache,
        collector=collector,
        compare_benchmark=compare,  # type: ignore[arg-type]
        stress_test=stress,
    )
    _perf = container
    app.state.performance = container

    await orchestrator.start()
    logger.info("Performance module initialized | backend={}", perf_cfg.backend.type)
    return container


async def shutdown_performance_module(app=None) -> None:
    global _perf
    container = _perf or getattr(getattr(app, "state", None), "performance", None)
    if container is not None:
        await container.orchestrator.stop()
    _perf = None


def get_performance(request: Request) -> PerformanceContainer:
    container = getattr(request.app.state, "performance", None)
    if container is None:
        raise RuntimeError("Performance module chưa khởi tạo.")
    return container
