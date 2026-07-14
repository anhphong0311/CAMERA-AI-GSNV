"""
Client Redis — dùng cho cache, session JWT revoke (sprint sau), pub/sub.

Sprint 1: chỉ kiểm tra kết nối qua health check.
"""

from redis.asyncio import Redis

from app.config.settings import get_settings

_redis_client: Redis | None = None


async def init_redis() -> None:
    """
    Khởi tạo kết nối Redis async.

    Gọi trong lifespan startup của FastAPI.
    """
    global _redis_client
    settings = get_settings()
    _redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    # Ping để xác nhận kết nối sớm
    await _redis_client.ping()


async def close_redis() -> None:
    """Đóng kết nối Redis khi shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def get_redis() -> Redis:
    """
    Trả về Redis client đã khởi tạo.

    Raises:
        RuntimeError: Nếu init_redis() chưa được gọi.
    """
    if _redis_client is None:
        raise RuntimeError("Redis chưa được khởi tạo. Gọi init_redis() trước.")
    return _redis_client


async def check_redis_connection() -> bool:
    """
    Kiểm tra Redis còn hoạt động (dùng cho /health).

    Returns:
        bool: True nếu ping thành công.
    """
    try:
        client = get_redis()
        await client.ping()
        return True
    except Exception:
        return False
