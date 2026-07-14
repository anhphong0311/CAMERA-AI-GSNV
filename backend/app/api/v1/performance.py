"""
Performance API (Sprint 10) — /system/performance, /gpu, /benchmark, /queue, /worker.

Mount dưới prefix /system (bổ sung admin system routes).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.modules.admin.dependencies import require_permission
from app.modules.performance.dependencies import PerformanceContainer, get_performance
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/system", tags=["Performance & Scaling"])


class BenchmarkBody(BaseModel):
    backends: Optional[list[str]] = None
    runs: int = Field(default=50, ge=5, le=200)
    warmup: int = Field(default=5, ge=0, le=20)
    image_size: Optional[int] = None


class StressBody(BaseModel):
    camera_counts: Optional[list[int]] = None
    duration_s: int = Field(default=5, ge=1, le=60)


@router.get("/performance", response_model=ApiResponse[dict])
async def system_performance(
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[dict]:
    """Snapshot hiệu năng: CPU/GPU/FPS/queue/delay/workers."""
    return ApiResponse(data=perf.collector.performance_report())


@router.get("/gpu", response_model=ApiResponse[list])
async def system_gpu(
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[list]:
    """Thông tin GPU, VRAM, temperature, camera assignment."""
    return ApiResponse(data=perf.gpu_manager.snapshot())


@router.post("/benchmark", response_model=ApiResponse[dict])
async def system_benchmark(
    body: BenchmarkBody | None = None,
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[dict]:
    """Benchmark so sánh PyTorch / ONNX / TensorRT."""
    req = body or BenchmarkBody()
    data = perf.compare_benchmark.run(
        backends=req.backends, runs=req.runs, warmup=req.warmup, image_size=req.image_size,
    )
    return ApiResponse(data=data)


@router.get("/queue", response_model=ApiResponse[dict])
async def system_queue(
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[dict]:
    """Trạng thái queue: frame scheduler, frame pool, AI pipeline."""
    return ApiResponse(
        data={
            "frame_scheduler": perf.frame_scheduler.summary(),
            "frame_pool": perf.frame_pool.stats(),
            "pipeline": perf.orchestrator.stats(),
            "cache": perf.cache.status(),
        }
    )


@router.get("/worker", response_model=ApiResponse[list])
async def system_workers(
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[list]:
    """Trạng thái worker pools."""
    return ApiResponse(data=perf.worker_registry.all_stats())


@router.post("/stress", response_model=ApiResponse[dict])
async def system_stress(
    request: Request,
    body: StressBody | None = None,
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[dict]:
    """Stress test multi-camera (synthetic load qua AI pipeline)."""
    req = body or StressBody()
    ai = getattr(request.app.state, "ai_service", None)

    def submit(cam_id: int, frame, fid: int) -> None:
        if perf.frame_scheduler.should_process(cam_id) and ai is not None:
            ai.submit_frame(cam_id, frame, fid)

    data = perf.stress_test.run(
        submit, camera_counts=req.camera_counts, duration_s=req.duration_s,
    )
    return ApiResponse(data=data)


@router.get("/performance/history", response_model=ApiResponse[list])
async def performance_history(
    limit: int = Query(60, ge=1, le=120),
    perf: PerformanceContainer = Depends(get_performance),
    _: dict = Depends(require_permission("system:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=perf.collector.history(limit))
