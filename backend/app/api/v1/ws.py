"""
Realtime API (Sprint 8) — WebSocket + REST snapshot cho Dashboard.

- WS   /ws                    → stream detection/tracking/alert/system realtime
- GET  /realtime/overview     → tổng quan (camera online/offline, FPS, alerts hôm nay)
- GET  /realtime/system       → snapshot system metrics
- GET  /realtime/alerts       → alert gần đây (realtime buffer)
- GET  /realtime/cameras      → trạng thái camera
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from app.modules.realtime.broadcaster import RealtimeBroadcaster
from app.modules.realtime.dependencies import get_broadcaster, get_manager
from app.modules.realtime.hub import ConnectionManager
from app.schemas.common import ApiResponse

router = APIRouter(tags=["Realtime"])


@router.websocket("/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    """Kênh WebSocket realtime cho Dashboard."""
    manager: ConnectionManager | None = getattr(
        websocket.app.state, "realtime_manager", None
    )
    if manager is None:
        await websocket.close(code=1011)
        return

    await manager.connect(websocket)
    await manager.send_personal(
        websocket, {"channel": "hello", "data": {"message": "connected"}}
    )
    try:
        while True:
            # nhận ping/subscribe từ client (giữ kết nối); bỏ qua nội dung
            msg = await websocket.receive_text()
            if msg == "ping":
                await manager.send_personal(websocket, {"channel": "pong", "data": {}})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as exc:  # pragma: no cover
        logger.warning("WS lỗi: {}", exc)
        await manager.disconnect(websocket)


realtime_router = APIRouter(prefix="/realtime", tags=["Realtime"])


@realtime_router.get("/overview", response_model=ApiResponse[dict])
async def overview(
    b: RealtimeBroadcaster = Depends(get_broadcaster),
) -> ApiResponse[dict]:
    """Tổng quan Dashboard."""
    return ApiResponse(data=b.overview())


@realtime_router.get("/system", response_model=ApiResponse[dict])
async def system(
    b: RealtimeBroadcaster = Depends(get_broadcaster),
) -> ApiResponse[dict]:
    """Snapshot system metrics."""
    return ApiResponse(data=b.latest_system())


@realtime_router.get("/alerts", response_model=ApiResponse[list])
async def alerts(
    limit: int = 50, b: RealtimeBroadcaster = Depends(get_broadcaster)
) -> ApiResponse[list]:
    """Alert realtime gần đây."""
    return ApiResponse(data=b.recent_alerts(limit))


@realtime_router.get("/cameras", response_model=ApiResponse[list])
async def cameras(
    b: RealtimeBroadcaster = Depends(get_broadcaster),
) -> ApiResponse[list]:
    """Trạng thái camera."""
    return ApiResponse(data=b.camera_status())


@realtime_router.get("/connections", response_model=ApiResponse[dict])
async def connections(
    m: ConnectionManager = Depends(get_manager),
) -> ApiResponse[dict]:
    """Số client WebSocket đang kết nối."""
    return ApiResponse(data={"active": m.active, "total": m.total_connected})
