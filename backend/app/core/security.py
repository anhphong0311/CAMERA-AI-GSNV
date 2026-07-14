"""
Tiện ích bảo mật: hash mật khẩu (Argon2) và JWT encode/decode.

Sprint 1: cung cấp hàm nền tảng; logic đăng nhập đầy đủ ở sprint sau.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import get_settings

# Hash mật khẩu: ưu tiên Argon2 (nếu backend khả dụng), fallback pbkdf2_sha256
# (thuần Python, luôn sẵn có). Cả hai scheme đều verify được — an toàn khi
# triển khai môi trường không cài argon2-cffi.
try:  # pragma: no cover - phụ thuộc môi trường
    import argon2 as _argon2  # noqa: F401

    _SCHEMES = ["argon2", "pbkdf2_sha256"]
except Exception:  # pragma: no cover
    _SCHEMES = ["pbkdf2_sha256", "argon2"]

_pwd_context = CryptContext(schemes=_SCHEMES, deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash mật khẩu plaintext bằng Argon2.

    Args:
        plain_password: Mật khẩu người dùng nhập.

    Returns:
        str: Chuỗi hash an toàn để lưu DB.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    So sánh mật khẩu plaintext với hash trong database.

    Args:
        plain_password: Mật khẩu người dùng nhập.
        hashed_password: Hash đã lưu trong DB.

    Returns:
        bool: True nếu khớp.
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | UUID,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Tạo JWT access token.

    Args:
        subject: Định danh user (thường là user UUID).
        extra_claims: Claim bổ sung (role, permissions...).

    Returns:
        str: JWT đã ký.
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Giải mã và xác thực JWT.

    Args:
        token: Chuỗi JWT.

    Returns:
        dict: Payload đã decode.

    Raises:
        JWTError: Token không hợp lệ hoặc hết hạn.
    """
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
