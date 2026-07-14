"""
Service layer — chứa logic nghiệp vụ (Sprint 1: skeleton).

Service gọi Repository, không trực tiếp phụ thuộc FastAPI Request/Response.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import check_redis_connection
from app.schemas.common import HealthData


class HealthService:
    """
    Kiểm tra sức khỏe hệ thống — PostgreSQL + Redis.

    Dùng bởi GET /health để Docker/K8s readiness probe.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check(self) -> HealthData:
        """
        Ping PostgreSQL và Redis, tổng hợp trạng thái.

        Returns:
            HealthData: Trạng thái tổng thể và từng component.
        """
        postgres_ok = await self._check_postgres()
        redis_ok = await check_redis_connection()
        overall = "healthy" if (postgres_ok and redis_ok) else "degraded"
        if not postgres_ok:
            overall = "unhealthy"
        return HealthData(status=overall, postgres=postgres_ok, redis=redis_ok)

    async def _check_postgres(self) -> bool:
        """Thực thi SELECT 1 để xác nhận PostgreSQL hoạt động."""
        try:
            await self.session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
