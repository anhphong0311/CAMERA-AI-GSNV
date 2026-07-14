"""
Event Processing Center API — Sprint 7 (mount dưới /api/v1).

Lưu ý: prefix `/processing` để KHÔNG đụng router `/events` của Sprint 6
(Rule Engine). Đây là các event ĐÃ XỬ LÝ (EventRecord + evidence + notification).

- GET  /processing/events                → danh sách event record
- GET  /processing/events/live           → event đang xử lý
- GET  /processing/events/history        → lịch sử event
- GET  /processing/events/statistics     → thống kê
- GET  /processing/events/{event_id}     → chi tiết event record
- POST /processing/events/ingest         → nạp event thủ công
- POST /processing/events/retry          → xử lý/gửi lại
- POST /processing/events/resend         → gửi lại (bỏ qua dedup/cooldown)
- GET  /processing/notifications         → lịch sử notification
- GET  /processing/telegram/status       → trạng thái Telegram
- POST /processing/telegram/command      → thử command bot
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.exceptions.base import NotFoundError
from app.modules.event.dependencies import get_event_service
from app.modules.event.exceptions import EventNotFoundError
from app.modules.event.schemas import (
    BehaviorEventInput,
    IngestEventRequest,
    ResendRequest,
    RetryRequest,
)
from app.modules.event.services import EventService
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/processing", tags=["Event Processing"])


@router.get("/events", response_model=ApiResponse[list])
async def list_events(
    camera_id: Optional[int] = Query(default=None),
    rule_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[list]:
    """Danh sách event record."""
    return ApiResponse(
        data=[e.to_dict() for e in service.list_events(camera_id, rule_id, limit)]
    )


@router.get("/events/live", response_model=ApiResponse[list])
async def live_events(
    service: EventService = Depends(get_event_service),
) -> ApiResponse[list]:
    """Event đang xử lý (chưa COMPLETED/FAILED)."""
    return ApiResponse(data=[e.to_dict() for e in service.live_events()])


@router.get("/events/history", response_model=ApiResponse[list])
async def event_history(
    camera_id: Optional[int] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[list]:
    """Lịch sử event record."""
    return ApiResponse(data=[e.to_dict() for e in service.event_history(camera_id, limit)])


@router.get("/events/statistics", response_model=ApiResponse[dict])
async def statistics(
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Thống kê Event Center."""
    return ApiResponse(data=service.statistics())


@router.post("/events/ingest", response_model=ApiResponse[dict])
async def ingest_event(
    body: IngestEventRequest,
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Nạp + xử lý một event thủ công (test/tích hợp ngoài)."""
    event = BehaviorEventInput.from_dict(body.model_dump())
    record = service.ingest_now(event)
    return ApiResponse(data=record.to_dict() if record else {})


@router.post("/events/retry", response_model=ApiResponse[dict])
async def retry_event(
    body: RetryRequest,
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Xử lý/gửi lại notification cho event."""
    try:
        record = service.retry(body.event_id)
    except EventNotFoundError as exc:
        raise NotFoundError("Event", body.event_id) from exc
    return ApiResponse(data=record.to_dict())


@router.post("/events/resend", response_model=ApiResponse[dict])
async def resend_event(
    body: ResendRequest,
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Gửi lại notification (bỏ qua dedup/cooldown)."""
    try:
        record = service.resend(body.event_id, force=body.force)
    except EventNotFoundError as exc:
        raise NotFoundError("Event", body.event_id) from exc
    return ApiResponse(data=record.to_dict())


@router.get("/events/{event_id}", response_model=ApiResponse[dict])
async def get_event(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Chi tiết một event record."""
    try:
        record = service.get_event(event_id)
    except EventNotFoundError as exc:
        raise NotFoundError("Event", event_id) from exc
    return ApiResponse(data=record.to_dict())


@router.get("/notifications", response_model=ApiResponse[list])
async def notifications(
    limit: int = Query(default=200, ge=1, le=2000),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[list]:
    """Lịch sử notification."""
    return ApiResponse(data=service.notifications(limit))


@router.get("/telegram/status", response_model=ApiResponse[dict])
async def telegram_status(
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Trạng thái Telegram + queue."""
    return ApiResponse(data=service.telegram_status())


@router.post("/telegram/test", response_model=ApiResponse[dict])
async def telegram_test(
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Gửi một tin test vào nhóm Telegram đã cấu hình."""
    return ApiResponse(data=service.send_test_notification())


@router.post("/telegram/command", response_model=ApiResponse[dict])
async def telegram_command(
    command: str = Query(..., description="Ví dụ: /status, /bat, /tat"),
    service: EventService = Depends(get_event_service),
) -> ApiResponse[dict]:
    """Thử một command bot (trả text phản hồi)."""
    response = await service.handle_command(command)
    return ApiResponse(data={"command": command, "response": response})
