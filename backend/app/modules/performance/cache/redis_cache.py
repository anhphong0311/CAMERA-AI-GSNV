"""
Redis cache layer (Sprint 10) — event/rule/camera/employee cache.

Best-effort: nếu Redis không khả dụng, fallback no-op (không crash).
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from app.modules.performance.config.loader import CacheConfig


class RedisCache:
    """Cache JSON values với TTL — prefix theo loại dữ liệu."""

    def __init__(self, config: CacheConfig) -> None:
        self._config = config
        self._available = False

    async def connect(self) -> None:
        if not self._config.enabled:
            return
        try:
            from app.core.redis import check_redis_connection

            self._available = bool(await check_redis_connection())
        except Exception:
            self._available = False

    async def get(self, category: str, key: str) -> Optional[Any]:
        if not self._available:
            return None
        prefix = self._config.prefixes.get(category, f"cache:{category}:")
        try:
            from app.core.redis import get_redis

            raw = await get_redis().get(f"{prefix}{key}")
            return json.loads(raw) if raw else None
        except Exception as exc:
            logger.debug("Cache get miss: {}", exc)
            return None

    async def set(self, category: str, key: str, value: Any) -> bool:
        if not self._available:
            return False
        prefix = self._config.prefixes.get(category, f"cache:{category}:")
        try:
            from app.core.redis import get_redis

            await get_redis().setex(
                f"{prefix}{key}",
                self._config.ttl_seconds,
                json.dumps(value, default=str),
            )
            return True
        except Exception as exc:
            logger.debug("Cache set failed: {}", exc)
            return False

    async def delete(self, category: str, key: str) -> None:
        if not self._available:
            return
        prefix = self._config.prefixes.get(category, f"cache:{category}:")
        try:
            from app.core.redis import get_redis

            await get_redis().delete(f"{prefix}{key}")
        except Exception:
            pass

    def status(self) -> dict:
        return {"enabled": self._config.enabled, "connected": self._available, "ttl_seconds": self._config.ttl_seconds}
