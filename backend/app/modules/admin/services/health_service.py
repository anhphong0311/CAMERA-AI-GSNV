"""
Health Monitor Service (Sprint 9).

Kiểm tra: Database, Redis, Camera, GPU, Storage, Telegram, API, WebSocket.
Các check được đăng ký dạng callable (đồng bộ/bất đồng bộ) → module độc lập, không
truy cập trực tiếp DB module khác.
"""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Union

CheckFunc = Callable[[], Union[Dict[str, Any], Awaitable[Dict[str, Any]]]]

# Thành phần bắt buộc khoẻ để hệ thống 'healthy'
CRITICAL = {"database", "api"}


class HealthMonitorService:
    def __init__(self) -> None:
        self._checks: Dict[str, CheckFunc] = {
            "api": lambda: {"ok": True, "detail": "running"},
            "storage": self._check_storage,
        }

    def register(self, name: str, func: CheckFunc) -> None:
        self._checks[name] = func

    @staticmethod
    def _check_storage() -> Dict[str, Any]:
        try:
            total, used, free = shutil.disk_usage(str(Path(".")))
            percent = round(used / total * 100, 1) if total else 0.0
            ok = free > 1e9  # còn > 1GB
            return {"ok": ok, "detail": f"{percent}% used", "free_gb": round(free / 1e9, 2)}
        except OSError as exc:  # pragma: no cover
            return {"ok": False, "detail": str(exc)}

    async def check_all(self) -> Dict[str, Any]:
        components: Dict[str, Any] = {}
        for name, func in self._checks.items():
            try:
                result = func()
                if inspect.isawaitable(result):
                    result = await result
                components[name] = result
            except Exception as exc:  # noqa: BLE001
                components[name] = {"ok": False, "detail": str(exc)}

        critical_ok = all(
            components.get(c, {}).get("ok", False) for c in CRITICAL if c in components
        )
        all_ok = all(c.get("ok", False) for c in components.values())
        if not critical_ok:
            status = "unhealthy"
        elif not all_ok:
            status = "degraded"
        else:
            status = "healthy"
        return {"status": status, "components": components}
