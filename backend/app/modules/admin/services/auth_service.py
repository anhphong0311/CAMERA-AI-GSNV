"""
Authentication Service (Sprint 9).

JWT access/refresh, refresh rotation, session timeout, logout all devices,
password expiration. Ghi audit mọi sự kiện đăng nhập/đăng xuất.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from jose import JWTError

from app.exceptions.base import UnauthorizedError
from app.core.security import verify_password
from app.modules.admin.rbac import expand_permissions, inherited_permissions
from app.modules.admin.repositories.base import (
    RoleRepository,
    SessionRepository,
    UserRepository,
)
from app.modules.admin.repositories.entities import SessionEntity, UserEntity
from app.modules.admin.security.password_policy import is_password_expired
from app.modules.admin.security.tokens import TokenPair, create_token_pair, verify_token
from app.modules.admin.services.audit_service import AuditService
from app.modules.admin.services.config_service import ConfigService


class AuthService:
    """Xác thực & quản lý phiên đăng nhập."""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        session_repo: SessionRepository,
        config: ConfigService,
        audit: AuditService,
    ) -> None:
        self._users = user_repo
        self._roles = role_repo
        self._sessions = session_repo
        self._config = config
        self._audit = audit

    # ----- Helpers -----
    def resolve_permissions(self, role_name: str) -> List[str]:
        role = self._roles.get(role_name)
        matrix = {r.name: r.permissions for r in self._roles.list()}
        base = expand_permissions(role.permissions) if role else set()
        return sorted(base | inherited_permissions(role_name, matrix))

    def _issue(self, user: UserEntity, remember: bool, ip: Optional[str], device: Optional[str]) -> Dict[str, Any]:
        perms = self.resolve_permissions(user.role)
        pair: TokenPair = create_token_pair(user.id, user.role, perms, remember)
        self._sessions.add(
            SessionEntity(
                user_id=user.id,
                refresh_jti=pair.refresh_jti,
                access_jti=pair.access_jti,
                device=device,
                ip=ip,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=pair.refresh_expires_in),
            )
        )
        return {
            "access_token": pair.access_token,
            "refresh_token": pair.refresh_token,
            "token_type": "bearer",
            "expires_in": pair.expires_in,
            "user": user.public(),
            "permissions": perms,
            "must_change_password": is_password_expired(
                user.password_changed_at, self._config.password_policy()
            ),
        }

    # ----- Public API -----
    def login(
        self,
        username: str,
        password: str,
        *,
        remember: bool = False,
        ip: Optional[str] = None,
        device: Optional[str] = None,
    ) -> Dict[str, Any]:
        user = self._users.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            self._audit.log(
                "login", "auth", username=username, status="failed", ip=ip,
                detail={"reason": "invalid_credentials"},
            )
            raise UnauthorizedError("Sai tài khoản hoặc mật khẩu.")
        if not user.is_active:
            self._audit.log(
                "login", "auth", user_id=user.id, username=username,
                status="failed", ip=ip, detail={"reason": "disabled"},
            )
            raise UnauthorizedError("Tài khoản đã bị vô hiệu hoá.")

        result = self._issue(user, remember, ip, device)
        user.last_login_at = datetime.now(timezone.utc)
        self._users.save(user)
        self._audit.log("login", "auth", user_id=user.id, username=username, ip=ip)
        return result

    def refresh(self, refresh_token: str, *, ip: Optional[str] = None) -> Dict[str, Any]:
        try:
            payload = verify_token(refresh_token, "refresh")
        except JWTError as exc:
            raise UnauthorizedError("Refresh token không hợp lệ.") from exc

        refresh_jti = payload.get("jti", "")
        session = self._sessions.get_by_refresh(refresh_jti)
        if session is None or session.revoked:
            raise UnauthorizedError("Phiên đã kết thúc, vui lòng đăng nhập lại.")

        # Session timeout theo cấu hình
        timeout = self._config.session_timeout_minutes()
        if timeout > 0:
            last = session.last_activity
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - last > timedelta(minutes=timeout):
                self._sessions.revoke(refresh_jti)
                raise UnauthorizedError("Phiên hết hạn do không hoạt động.")

        user = self._users.get(session.user_id)
        if user is None or not user.is_active:
            self._sessions.revoke(refresh_jti)
            raise UnauthorizedError("Tài khoản không khả dụng.")

        # Rotation: thu hồi refresh cũ, phát cặp mới
        self._sessions.revoke(refresh_jti)
        result = self._issue(user, remember=False, ip=ip, device=session.device)
        self._audit.log("refresh", "auth", user_id=user.id, username=user.username, ip=ip)
        return result

    def logout(self, refresh_token: str, *, ip: Optional[str] = None) -> None:
        try:
            payload = verify_token(refresh_token, "refresh")
        except JWTError:
            return
        refresh_jti = payload.get("jti", "")
        session = self._sessions.get_by_refresh(refresh_jti)
        self._sessions.revoke(refresh_jti)
        if session is not None:
            self._audit.log("logout", "auth", user_id=session.user_id, ip=ip)

    def logout_all(self, user_id: str, *, ip: Optional[str] = None) -> int:
        count = self._sessions.revoke_all(user_id)
        self._audit.log(
            "logout_all", "auth", user_id=user_id, ip=ip, detail={"revoked": count}
        )
        return count

    def me(self, user_id: str) -> Dict[str, Any]:
        user = self._users.get(user_id)
        if user is None:
            raise UnauthorizedError("Người dùng không tồn tại.")
        return {"user": user.public(), "permissions": self.resolve_permissions(user.role)}

    def sessions(self, user_id: str) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._sessions.list_for_user(user_id) if not s.revoked]
