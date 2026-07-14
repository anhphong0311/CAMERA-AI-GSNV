"""
AI Detection API — Sprint 3.

Endpoints (mount dưới /api/v1):
- GET  /ai/model        → thông tin model
- POST /ai/reload       → reload model
- POST /ai/inference    → detect object trên 1 ảnh base64
- POST /ai/benchmark    → benchmark hiệu năng
- GET  /ai/statistics   → thống kê inference

KHÔNG tracking/telegram/rule engine/DB.
"""

from fastapi import APIRouter, Depends

from app.modules.ai.dependencies import get_benchmark_service, get_detection_service
from app.modules.ai.schemas.detection import (
    BenchmarkRequest,
    InferenceRequest,
    ReloadRequest,
)
from app.modules.ai.services.benchmark_service import BenchmarkService
from app.modules.ai.services.detection_service import DetectionService
from app.modules.ai.utils.image_io import decode_base64_image, encode_image_base64
from app.modules.ai.utils.visualizer import draw_detections
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/ai", tags=["AI Detection"])


@router.get("/model", response_model=ApiResponse[dict])
async def get_model(
    service: DetectionService = Depends(get_detection_service),
) -> ApiResponse[dict]:
    """Thông tin model đang nạp."""
    return ApiResponse(data=service.get_model_info().to_dict())


@router.post("/reload", response_model=ApiResponse[dict])
async def reload_model(
    body: ReloadRequest | None = None,
    service: DetectionService = Depends(get_detection_service),
) -> ApiResponse[dict]:
    """Reload model (đổi weight/thiết bị theo config hiện tại)."""
    info = service.reload_model()
    return ApiResponse(data=info.to_dict())


@router.post("/inference", response_model=ApiResponse[dict])
async def run_inference(
    body: InferenceRequest,
    service: DetectionService = Depends(get_detection_service),
) -> ApiResponse[dict]:
    """
    Chạy detection trên một ảnh base64 → DetectionResult JSON.

    Nếu visualize=true, trả kèm ảnh overlay bbox (base64) để debug.
    """
    frame = decode_base64_image(body.image_base64)
    result = service.infer_frame(frame, body.camera_id, body.frame_id)
    payload = result.to_dict()

    if body.visualize:
        overlay = draw_detections(frame, result, camera_name=f"cam-{body.camera_id}")
        payload["overlay_base64"] = encode_image_base64(overlay)

    return ApiResponse(data=payload)


@router.post("/benchmark", response_model=ApiResponse[dict])
async def run_benchmark(
    body: BenchmarkRequest | None = None,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> ApiResponse[dict]:
    """Benchmark hiệu năng inference (FPS, thời gian, CPU/GPU/VRAM)."""
    req = body or BenchmarkRequest()
    result = service.run(runs=req.runs, image_size=req.image_size, warmup=req.warmup)
    return ApiResponse(data=result.to_dict())


@router.get("/statistics", response_model=ApiResponse[dict])
async def get_statistics(
    service: DetectionService = Depends(get_detection_service),
) -> ApiResponse[dict]:
    """Thống kê inference tích lũy + trạng thái pipeline."""
    return ApiResponse(data=service.get_statistics())
