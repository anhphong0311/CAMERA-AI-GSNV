"""Alerts API skeleton — danh sách và chi tiết cảnh báo."""

from fastapi import APIRouter

from app.schemas.common import ApiResponse, MessageResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=ApiResponse[MessageResponse])
async def list_alerts() -> ApiResponse[MessageResponse]:
    """Danh sách alerts — skeleton."""
    return ApiResponse(data=MessageResponse(message="GET /alerts — sprint 2"))


@router.get("/{alert_id}", response_model=ApiResponse[MessageResponse])
async def get_alert(alert_id: str) -> ApiResponse[MessageResponse]:
    """Chi tiết alert — skeleton."""
    return ApiResponse(
        data=MessageResponse(message=f"GET /alerts/{alert_id} — sprint 2")
    )
