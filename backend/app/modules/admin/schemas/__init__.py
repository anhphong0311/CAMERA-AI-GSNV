"""Pydantic schemas (DTO) cho API module admin (Sprint 9)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ----- Auth -----
class LoginBody(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1)
    remember: bool = False


class RefreshBody(BaseModel):
    refresh_token: str


class TokenResult(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    permissions: List[str]
    must_change_password: bool = False


# ----- Users -----
class UserCreateBody(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1)
    role: str = "viewer"
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None


class UserUpdateBody(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    avatar: Optional[str] = None


class ResetPasswordBody(BaseModel):
    new_password: str = Field(..., min_length=1)


# ----- Roles -----
class RoleCreateBody(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str = ""
    permissions: List[str] = Field(default_factory=list)


class RoleUpdateBody(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


# ----- Config -----
class ConfigSetBody(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: Any = None


# ----- Models -----
class ModelRegisterBody(BaseModel):
    name: str
    version: str
    path: str
    metrics: Optional[Dict[str, Any]] = None


class ModelBenchmarkBody(BaseModel):
    metrics: Dict[str, Any]


# ----- Backup / Restore -----
class BackupCreateBody(BaseModel):
    kind: str = Field(..., description="database|config|rule|roi|ai_config")


# ----- Scheduler -----
class JobToggleBody(BaseModel):
    enabled: bool
