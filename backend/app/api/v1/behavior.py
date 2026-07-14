"""
Behavior API — Sprint 5 (Human Pose & Behavior Feature Extraction).

Endpoints (mount dưới /api/v1):
- POST /behavior/process           → trích đặc trưng từ tracks (+frame +objects)
- GET  /behavior/live              → đặc trưng mới nhất mọi camera
- GET  /behavior/statistics        → thống kê
- GET  /behavior/camera/{cam_id}   → đặc trưng mới nhất một camera
- GET  /behavior/{track_id}        → đặc trưng mới nhất một track
- POST /behavior/benchmark         → benchmark pose/feature

KHÔNG rule engine / alert / telegram / dashboard / database / performance score.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends

from app.exceptions.base import NotFoundError
from app.modules.ai.models import BoundingBox, Detection
from app.modules.behavior.dependencies import (
    get_behavior_benchmark_service,
    get_behavior_service,
)
from app.modules.behavior.models import TrackingView, TrackView
from app.modules.behavior.schemas import BehaviorProcessRequest, BenchmarkRequest
from app.modules.behavior.services import BehaviorService, BenchmarkService
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/behavior", tags=["Behavior"])


def _to_tracking_view(body: BehaviorProcessRequest) -> TrackingView:
    """Chuyển request → TrackingView (duck-typed cho engine)."""
    ts = datetime.now(timezone.utc)
    if body.timestamp:
        try:
            ts = datetime.fromisoformat(body.timestamp)
        except ValueError:
            ts = datetime.now(timezone.utc)
    tracks = [
        TrackView(
            track_id=t.track_id,
            camera_id=body.camera_id,
            bbox=(t.bbox[0], t.bbox[1], t.bbox[2], t.bbox[3]),
            speed_px=t.speed_px,
            direction=t.direction,
            current_roi_id=t.roi,
        )
        for t in body.tracks
    ]
    return TrackingView(
        camera_id=body.camera_id, frame_id=body.frame_id, timestamp=ts, tracks=tracks
    )


def _to_detections(body: BehaviorProcessRequest) -> List[Detection]:
    """Chuyển objects request → Detection (ngữ cảnh)."""
    out: List[Detection] = []
    for o in body.objects:
        out.append(
            Detection(
                class_name=o.class_name,
                confidence=o.confidence,
                bbox=BoundingBox(*o.bbox),
                class_id=o.class_id,
            )
        )
    return out


@router.post("/process", response_model=ApiResponse[dict])
async def process(
    body: BehaviorProcessRequest,
    service: BehaviorService = Depends(get_behavior_service),
) -> ApiResponse[dict]:
    """Trích đặc trưng hành vi cho một frame → BehaviorResult JSON."""
    frame = None
    if body.frame:
        from app.modules.ai.utils.image_io import decode_base64_image

        frame = decode_base64_image(body.frame)
    tracking_view = _to_tracking_view(body)
    detections = _to_detections(body)
    result = service.process(frame, tracking_view, detections)
    return ApiResponse(data=result.to_dict())


@router.get("/live", response_model=ApiResponse[list])
async def get_live(
    service: BehaviorService = Depends(get_behavior_service),
) -> ApiResponse[list]:
    """Đặc trưng mới nhất của tất cả camera."""
    return ApiResponse(data=[r.to_dict() for r in service.get_live()])


@router.get("/statistics", response_model=ApiResponse[dict])
async def get_statistics(
    service: BehaviorService = Depends(get_behavior_service),
) -> ApiResponse[dict]:
    """Thống kê Behavior Engine."""
    return ApiResponse(data=service.statistics())


@router.post("/benchmark", response_model=ApiResponse[dict])
async def run_benchmark(
    body: BenchmarkRequest | None = None,
    service: BenchmarkService = Depends(get_behavior_benchmark_service),
) -> ApiResponse[dict]:
    """Benchmark pose/feature (FPS, latency, CPU/GPU/VRAM/Memory)."""
    req = body or BenchmarkRequest()
    result = service.run(
        frames=req.frames,
        people=req.people,
        width=req.width,
        height=req.height,
        use_real_pose=req.use_real_pose,
    )
    return ApiResponse(data=result.to_dict())


@router.get("/camera/{camera_id}", response_model=ApiResponse[dict])
async def get_camera(
    camera_id: int,
    service: BehaviorService = Depends(get_behavior_service),
) -> ApiResponse[dict]:
    """Đặc trưng mới nhất của một camera."""
    result = service.get_camera(camera_id)
    if result is None:
        raise NotFoundError("Behavior camera", camera_id)
    return ApiResponse(data=result.to_dict())


@router.get("/{track_id}", response_model=ApiResponse[dict])
async def get_track(
    track_id: int,
    service: BehaviorService = Depends(get_behavior_service),
) -> ApiResponse[dict]:
    """Đặc trưng hành vi mới nhất của một track."""
    dto = service.get_track(track_id)
    if dto is None:
        raise NotFoundError("Behavior track", track_id)
    return ApiResponse(data=dto.to_dict())
