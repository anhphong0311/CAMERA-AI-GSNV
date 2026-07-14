"""
Tracking API — Sprint 4.

Endpoints (mount dưới /api/v1):
- POST /tracking/process          → chạy tracking từ 1 DetectionResult
- GET  /tracking/live             → kết quả mới nhất mọi camera
- GET  /tracking/camera/{cam_id}  → kết quả mới nhất một camera
- GET  /tracking/track/{track_id} → chi tiết một track (kèm timeline)
- GET  /tracking/history          → lịch sử TrackingResult của một camera
- GET  /tracking/statistics       → thống kê tracking

KHÔNG detect/YOLO/pose/rule engine/telegram/DB/alert.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.exceptions.base import NotFoundError
from app.modules.ai.models import BoundingBox, Detection, DetectionResult, utc_now
from app.modules.tracking.benchmark.benchmark_service import BenchmarkService
from app.modules.tracking.dependencies import (
    get_tracking_benchmark_service,
    get_tracking_service,
)
from app.modules.tracking.schemas.tracking import (
    BenchmarkRequest,
    DetectionResultRequest,
)
from app.modules.tracking.services.tracking_service import TrackingService
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/tracking", tags=["Tracking"])


def _to_detection_result(body: DetectionResultRequest) -> DetectionResult:
    """Chuyển request JSON → DetectionResult DTO."""
    ts = utc_now()
    if body.timestamp:
        try:
            ts = datetime.fromisoformat(body.timestamp)
        except ValueError:
            ts = utc_now()
    objects = []
    for o in body.objects:
        if len(o.bbox) != 4:
            continue
        objects.append(
            Detection(
                class_name=o.class_name,
                confidence=o.confidence,
                bbox=BoundingBox(*o.bbox),
                class_id=o.class_id,
            )
        )
    return DetectionResult(
        camera_id=body.camera_id,
        frame_id=body.frame_id,
        timestamp=ts,
        objects=objects,
        width=body.width,
        height=body.height,
    )


@router.post("/process", response_model=ApiResponse[dict])
async def process_detection(
    body: DetectionResultRequest,
    service: TrackingService = Depends(get_tracking_service),
) -> ApiResponse[dict]:
    """Chạy tracking trên một DetectionResult → TrackingResult JSON."""
    detection = _to_detection_result(body)
    result = service.process(detection)
    return ApiResponse(data=result.to_dict())


@router.get("/live", response_model=ApiResponse[list])
async def get_live(
    service: TrackingService = Depends(get_tracking_service),
) -> ApiResponse[list]:
    """Kết quả tracking mới nhất của tất cả camera."""
    return ApiResponse(data=[r.to_dict() for r in service.get_live()])


@router.get("/statistics", response_model=ApiResponse[dict])
async def get_statistics(
    service: TrackingService = Depends(get_tracking_service),
) -> ApiResponse[dict]:
    """Thống kê tracking tổng hợp."""
    return ApiResponse(data=service.statistics())


@router.get("/history", response_model=ApiResponse[list])
async def get_history(
    camera_id: int = Query(..., description="ID camera"),
    service: TrackingService = Depends(get_tracking_service),
) -> ApiResponse[list]:
    """Lịch sử TrackingResult của một camera."""
    return ApiResponse(data=[r.to_dict() for r in service.get_history(camera_id)])


@router.post("/benchmark", response_model=ApiResponse[dict])
async def run_benchmark(
    body: BenchmarkRequest | None = None,
    service: BenchmarkService = Depends(get_tracking_benchmark_service),
) -> ApiResponse[dict]:
    """Benchmark tracking (FPS, ID switch, stability, CPU/memory)."""
    req = body or BenchmarkRequest()
    result = service.run(
        frames=req.frames,
        num_people=req.num_people,
        width=req.width,
        height=req.height,
    )
    return ApiResponse(data=result.to_dict())


@router.get("/camera/{camera_id}", response_model=ApiResponse[dict])
async def get_camera(
    camera_id: int,
    service: TrackingService = Depends(get_tracking_service),
) -> ApiResponse[dict]:
    """Kết quả tracking mới nhất của một camera."""
    result = service.get_camera_result(camera_id)
    if result is None:
        raise NotFoundError(f"Chưa có dữ liệu tracking cho camera {camera_id}")
    return ApiResponse(data=result.to_dict())


@router.get("/track/{track_id}", response_model=ApiResponse[dict])
async def get_track(
    track_id: int,
    camera_id: int | None = Query(
        default=None, description="Giới hạn theo camera (track id chỉ duy nhất trong camera)"
    ),
    service: TrackingService = Depends(get_tracking_service),
) -> ApiResponse[dict]:
    """Chi tiết một track (kèm timeline). Track id chỉ duy nhất trong phạm vi camera."""
    matches = service.find_track(track_id, camera_id)
    if not matches:
        raise NotFoundError(f"Không tìm thấy track {track_id}")
    return ApiResponse(
        data={
            "matches": [
                {"camera_id": cam_id, "track": track.to_detail_dict()}
                for cam_id, track in matches
            ]
        }
    )
