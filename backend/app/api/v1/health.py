"""
Health check endpoint — dùng cho Docker readiness/liveness probe.
Sprint 11: thêm /health/full cho deep check (Watchdog, production).
"""

from fastapi import APIRouter, Depends, Request

from app.dependencies import DbSession, get_health_service
from app.modules.ops.health import check_full
from app.schemas.common import ApiResponse, HealthData
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ApiResponse[HealthData])
async def health_check(
    service: HealthService = Depends(get_health_service),
) -> ApiResponse[HealthData]:
    """
    Kiểm tra trạng thái PostgreSQL và Redis (probe nhanh).

    Returns:
        ApiResponse chứa HealthData.
    """
    data = await service.check()
    return ApiResponse(data=data)


@router.get("/health/full", response_model=ApiResponse[dict])
async def health_check_full(request: Request) -> ApiResponse[dict]:
    """
    Deep health — Database, Redis, Camera, GPU, Storage, Telegram, AI Worker, Queue.
    Dùng cho Watchdog, Grafana, production monitoring.
    """
    data = await check_full(request.app)
    return ApiResponse(data=data)
