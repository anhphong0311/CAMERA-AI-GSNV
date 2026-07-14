"""
Pydantic schemas cho authentication.

Sprint 1: skeleton — login request/response, chưa có logic đăng nhập đầy đủ.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Body POST /auth/login."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """Response chứa JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Thời gian hết hạn access token (giây)")
