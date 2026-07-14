"""
FastAPI dependencies — Dependency Injection container.

Cung cấp session, services, và auth guard cho routes.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.services.health_service import HealthService

# Type alias cho session inject — dùng xuyên suốt API layer
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Bearer token scheme — dùng cho protected routes
_bearer_scheme = HTTPBearer(auto_error=False)


def get_health_service(session: DbSession) -> HealthService:
    """Factory inject HealthService."""
    return HealthService(session)


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> dict | None:
    """
    Dependency lấy user hiện tại từ JWT — optional (không bắt buộc auth).

    Legacy helper; enterprise auth uses admin module dependencies.

    Returns:
        dict | None: Payload user hoặc None nếu chưa đăng nhập.
    """
    if credentials is None:
        return None
    return {"sub": "skeleton-user", "token": credentials.credentials}
