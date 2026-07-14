"""
JWT tokens (Sprint 9) — access + refresh token với jti, type và rotation.

Xây trên `app.config.settings` (secret/alg/expiry). Thuần logic → test không cần DB.
Session/refresh rotation được quản lý ở SessionRepository (revoke theo jti).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, List

from jose import jwt

from app.config.settings import get_settings


@dataclass
class TokenPair:
    """Cặp token phát cho client."""

    access_token: str
    refresh_token: str
    access_jti: str
    refresh_jti: str
    expires_in: int  # access token TTL (giây)
    refresh_expires_in: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(payload: dict[str, Any]) -> str:
    settings = get_settings()
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(
    user_id: str,
    role: str,
    permissions: List[str],
    remember: bool = False,
) -> TokenPair:
    """Tạo access + refresh token. `remember` kéo dài TTL refresh."""
    settings = get_settings()
    access_ttl = settings.access_token_expire_minutes * 60
    refresh_minutes = settings.refresh_token_expire_minutes * (4 if remember else 1)
    refresh_ttl = refresh_minutes * 60

    now = _now()
    access_jti = uuid.uuid4().hex
    refresh_jti = uuid.uuid4().hex

    access_payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": access_jti,
        "role": role,
        "permissions": permissions,
        "iat": now,
        "exp": now + timedelta(seconds=access_ttl),
    }
    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": refresh_jti,
        "iat": now,
        "exp": now + timedelta(minutes=refresh_minutes),
    }
    return TokenPair(
        access_token=_encode(access_payload),
        refresh_token=_encode(refresh_payload),
        access_jti=access_jti,
        refresh_jti=refresh_jti,
        expires_in=access_ttl,
        refresh_expires_in=refresh_ttl,
    )


def verify_token(token: str, expected_type: str) -> dict[str, Any]:
    """Giải mã + kiểm tra loại token. Ném jose.JWTError nếu không hợp lệ."""
    settings = get_settings()
    payload = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        from jose import JWTError

        raise JWTError(f"Sai loại token: cần {expected_type}")
    return payload
