"""
API v1 router — gom tất cả endpoint skeleton Sprint 1.

Prefix: /api/v1 (đăng ký trong main.py).
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    alerts,
    behavior,
    cameras,
    dashboard,
    employees,
    event_processing,
    events,
    health,
    ml_platform,
    performance,
    rules,
    tracking,
    ws,
)

api_router = APIRouter()

api_router.include_router(health.router)

# Sprint 9 — Enterprise Admin routers (auth/users/roles/permissions/audit/config/
# system/storage/models/backup/restore/scheduler). Thay thế auth/users skeleton cũ.
for _admin_router in admin.ADMIN_ROUTERS:
    api_router.include_router(_admin_router)

# Sprint 10 — Performance & Scaling APIs (/system/performance, /gpu, /benchmark...)
api_router.include_router(performance.router)

# Sprint 13 — ML Platform (v2.0): dataset, annotation, training, model, benchmark, deployment
for _ml_router in ml_platform.ML_PLATFORM_ROUTERS:
    api_router.include_router(_ml_router)

api_router.include_router(employees.router)
api_router.include_router(cameras.router)
api_router.include_router(alerts.router)
api_router.include_router(rules.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
api_router.include_router(tracking.router)
api_router.include_router(behavior.router)
api_router.include_router(events.router)
api_router.include_router(event_processing.router)
api_router.include_router(ws.router)
api_router.include_router(ws.realtime_router)
