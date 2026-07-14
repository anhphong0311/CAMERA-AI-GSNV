"""Dashboard API skeleton — thống kê tổng quan (chưa có business logic)."""

from fastapi import APIRouter

from app.schemas.common import ApiResponse, MessageResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=ApiResponse[MessageResponse])
async def dashboard_summary() -> ApiResponse[MessageResponse]:
    """Tổng quan dashboard — skeleton."""
    return ApiResponse(
        data=MessageResponse(message="GET /dashboard/summary — sprint 2")
    )


@router.get("/stats", response_model=ApiResponse[MessageResponse])
async def dashboard_stats() -> ApiResponse[MessageResponse]:
    """Thống kê realtime — skeleton."""
    return ApiResponse(
        data=MessageResponse(message="GET /dashboard/stats — sprint 2")
    )
