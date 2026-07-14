"""
Deep Health Check (Sprint 11) — /health/full cho Docker, Watchdog, K8s.

Tổng hợp: Database, Redis, Camera, GPU, Storage, Telegram, AI Worker, Queue.
Gọi các service hiện có qua app.state — không truy cập DB module khác trực tiếp.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import text

from app.core.redis import check_redis_connection
from app.schemas.common import HealthData


async def check_basic(session) -> HealthData:
    """Health cơ bản (Sprint 1) — postgres + redis."""
    postgres_ok = False
    try:
        await session.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        pass
    redis_ok = await check_redis_connection()
    overall = "healthy" if (postgres_ok and redis_ok) else "degraded"
    if not postgres_ok:
        overall = "unhealthy"
    return HealthData(status=overall, postgres=postgres_ok, redis=redis_ok, version="1.0.0")


def _storage_check() -> Dict[str, Any]:
    try:
        total, used, free = shutil.disk_usage(".")
        pct = round(used / total * 100, 1) if total else 0
        ok = free > 500_000_000  # >500MB
        return {"ok": ok, "percent_used": pct, "free_gb": round(free / 1e9, 2)}
    except OSError as exc:
        return {"ok": False, "detail": str(exc)}


async def check_full(app) -> Dict[str, Any]:
    """Deep health — mọi component production."""
    components: Dict[str, Any] = {}

    # Database + Redis (basic)
    from app.core.database import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        basic = await check_basic(session)
        components["database"] = {"ok": basic.postgres, "detail": "connected" if basic.postgres else "down"}
        components["redis"] = {"ok": basic.redis, "detail": "connected" if basic.redis else "down"}

    # Admin health monitor (GPU, telegram, websocket, camera stubs)
    admin = getattr(app.state, "admin", None)
    if admin is not None:
        admin_health = await admin.health.check_all()
        for name, data in admin_health.get("components", {}).items():
            components[name] = data
    else:
        components["api"] = {"ok": True, "detail": "running"}

    # Performance / queue / AI worker
    perf = getattr(app.state, "performance", None)
    if perf is not None:
        components["gpu"] = {"ok": True, "devices": perf.gpu_manager.snapshot()}
        components["queue"] = {
            "ok": True,
            "frame_scheduler": perf.frame_scheduler.summary(),
            "pipeline": perf.orchestrator.stats(),
        }
        ai = getattr(app.state, "ai_service", None)
        if ai is not None:
            stats = ai.get_statistics()
            components["ai_worker"] = {
                "ok": stats.get("pipeline_running", False) or stats.get("model_loaded", False),
                "detail": stats,
            }
    else:
        components["ai_worker"] = {"ok": False, "detail": "performance module not loaded"}

    # Camera manager
    cam_mgr = getattr(app.state, "camera_manager", None)
    if cam_mgr is not None:
        workers = getattr(cam_mgr, "_workers", {})
        online = sum(1 for w in workers.values() if getattr(w, "is_running", False))
        components["camera"] = {
            "ok": True,
            "registered": len(workers),
            "online": online,
        }
    else:
        components["camera"] = {"ok": True, "detail": "not initialized"}

    components["storage"] = _storage_check()

    # Telegram — best effort from config
    components.setdefault("telegram", {"ok": True, "detail": "configured via config center"})

    critical = {"database", "redis", "api"}
    critical_ok = all(components.get(c, {}).get("ok", False) for c in critical if c in components)
    all_ok = all(c.get("ok", False) for c in components.values())
    if not critical_ok:
        status = "unhealthy"
    elif not all_ok:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "version": "1.0.0",
        "components": components,
    }
