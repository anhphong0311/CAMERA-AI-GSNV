"""
Camera API — Sprint 2 full CRUD + stream control.

Prefix: /api/v1/cameras (đăng ký trong api_router).
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.modules.camera.dependencies import get_camera_service
from app.modules.camera.models.frame import CameraRuntimeStatus
from app.modules.camera.schemas.camera import (
    CameraCreate,
    CameraFPSRead,
    CameraFrameRead,
    CameraHealthRead,
    CameraRead,
    CameraUpdate,
)
from app.modules.camera.services.camera_service import CameraService
from app.schemas.common import ApiResponse, MessageResponse

router = APIRouter(prefix="/cameras", tags=["Cameras"])


class RTSPTestBody(BaseModel):
    """Body kiểm tra kết nối RTSP (Camera Management — Sprint 9)."""

    url: str = Field(..., description="RTSP URL cần kiểm tra")
    timeout_s: float = Field(default=5.0, ge=1.0, le=30.0)


@router.post("/rtsp-test", response_model=ApiResponse[dict])
async def rtsp_test(body: RTSPTestBody) -> ApiResponse[dict]:
    """Thử mở RTSP stream và đọc 1 frame (best-effort, cần OpenCV)."""
    import asyncio

    def _probe() -> dict:
        import os

        try:
            import cv2  # type: ignore
        except Exception:  # pragma: no cover - OpenCV có thể chưa cài
            return {"ok": False, "detail": "OpenCV chưa được cài đặt trên server."}
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
        cap = cv2.VideoCapture(body.url, cv2.CAP_FFMPEG)
        try:
            if not cap.isOpened():
                return {"ok": False, "detail": "Không mở được RTSP stream."}
            ok, frame = cap.read()
            if not ok or frame is None:
                return {"ok": False, "detail": "Mở được stream nhưng không đọc được frame."}
            h, w = frame.shape[:2]
            return {"ok": True, "detail": "Kết nối thành công.", "width": int(w), "height": int(h)}
        finally:
            cap.release()

    try:
        result = await asyncio.wait_for(asyncio.to_thread(_probe), timeout=body.timeout_s + 2)
    except asyncio.TimeoutError:
        result = {"ok": False, "detail": "Hết thời gian chờ kết nối RTSP."}
    return ApiResponse(data=result)


@router.get("", response_model=ApiResponse[List[CameraRead]])
async def list_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[List[CameraRead]]:
    """Danh sách camera."""
    data = await service.list_cameras(skip=skip, limit=limit)
    return ApiResponse(data=data, meta={"total": len(data), "skip": skip, "limit": limit})


@router.get("/{camera_id}", response_model=ApiResponse[CameraRead])
async def get_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[CameraRead]:
    """Chi tiết camera."""
    return ApiResponse(data=await service.get_camera(camera_id))


@router.post("", response_model=ApiResponse[CameraRead], status_code=201)
async def create_camera(
    body: CameraCreate,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[CameraRead]:
    """Thêm camera mới."""
    return ApiResponse(data=await service.create_camera(body))


@router.put("/{camera_id}", response_model=ApiResponse[CameraRead])
async def update_camera(
    camera_id: int,
    body: CameraUpdate,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[CameraRead]:
    """Cập nhật camera."""
    return ApiResponse(data=await service.update_camera(camera_id, body))


@router.delete("/{camera_id}", response_model=ApiResponse[MessageResponse])
async def delete_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[MessageResponse]:
    """Xóa camera."""
    await service.delete_camera(camera_id)
    return ApiResponse(data=MessageResponse(message=f"Camera {camera_id} đã xóa."))


@router.post("/{camera_id}/start", response_model=ApiResponse[dict])
async def start_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[dict]:
    """Bắt đầu đọc RTSP stream."""
    status: CameraRuntimeStatus = await service.start_stream(camera_id)
    return ApiResponse(data=status.to_dict())


@router.post("/{camera_id}/stop", response_model=ApiResponse[MessageResponse])
async def stop_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[MessageResponse]:
    """Dừng worker camera."""
    await service.stop_stream_async(camera_id)
    return ApiResponse(data=MessageResponse(message=f"Camera {camera_id} đã dừng."))


@router.post("/{camera_id}/restart", response_model=ApiResponse[dict])
async def restart_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[dict]:
    """Restart worker camera."""
    status = await service.restart_stream(camera_id)
    return ApiResponse(data=status.to_dict())


@router.get("/{camera_id}/health", response_model=ApiResponse[CameraHealthRead])
async def camera_health(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[CameraHealthRead]:
    """Health check camera — DB + runtime."""
    return ApiResponse(data=await service.get_health(camera_id))


@router.get("/{camera_id}/fps", response_model=ApiResponse[CameraFPSRead])
async def camera_fps(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[CameraFPSRead]:
    """FPS metrics camera (worker phải đang chạy)."""
    return ApiResponse(data=service.get_fps(camera_id))


@router.get("/{camera_id}/frame", response_model=ApiResponse[CameraFrameRead])
async def camera_frame(
    camera_id: int,
    service: CameraService = Depends(get_camera_service),
) -> ApiResponse[CameraFrameRead]:
    """Frame mới nhất — JPEG base64 (encode off event-loop)."""
    import asyncio

    data = await asyncio.to_thread(service.get_latest_frame, camera_id)
    return ApiResponse(data=data)
