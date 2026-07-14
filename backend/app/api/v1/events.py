"""
Events API — Sprint 6 (Behavior Event do Rule Engine tạo).

Endpoints (mount dưới /api/v1):
- GET /events            → lịch sử event (lọc camera_id/track_id/rule_id)
- GET /events/live       → event đang hoạt động
- GET /events/history    → lịch sử event
- GET /events/statistics → thống kê event
- GET /events/queue      → AlertQueue đang chờ (Sprint 7 tiêu thụ)

KHÔNG Telegram / Database / Dashboard.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.modules.rule_engine.dependencies import get_rule_service
from app.modules.rule_engine.services import RuleService
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=ApiResponse[list])
async def list_events(
    camera_id: Optional[int] = Query(default=None),
    track_id: Optional[int] = Query(default=None),
    rule_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[list]:
    """Lịch sử event (mặc định)."""
    events = service.event_history(camera_id, track_id, rule_id, limit)
    return ApiResponse(data=[e.to_dict() for e in events])


@router.get("/live", response_model=ApiResponse[list])
async def live_events(
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[list]:
    """Event đang hoạt động (chưa kết thúc)."""
    return ApiResponse(data=[e.to_dict() for e in service.live_events()])


@router.get("/history", response_model=ApiResponse[list])
async def event_history(
    camera_id: Optional[int] = Query(default=None),
    track_id: Optional[int] = Query(default=None),
    rule_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[list]:
    """Lịch sử event."""
    events = service.event_history(camera_id, track_id, rule_id, limit)
    return ApiResponse(data=[e.to_dict() for e in events])


@router.get("/statistics", response_model=ApiResponse[dict])
async def event_statistics(
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Thống kê event."""
    return ApiResponse(data=service.statistics()["events"])


@router.get("/queue", response_model=ApiResponse[list])
async def alert_queue(
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[list]:
    """Xem AlertQueue đang chờ (không xóa)."""
    return ApiResponse(
        data=[e.to_dict() for e in service.alert_queue().peek_all()]
    )
