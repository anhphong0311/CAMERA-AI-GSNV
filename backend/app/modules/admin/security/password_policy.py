"""
Password Policy (Sprint 9) — chính sách mật khẩu Enterprise.

Thuần logic (không phụ thuộc DB/framework) → dễ unit test. Cấu hình có thể nạp
từ Configuration Center (DB) và truyền vào, KHÔNG hardcode ngưỡng trong code gọi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List

# Danh sách mật khẩu phổ biến bị cấm (rút gọn — có thể mở rộng qua config).
_COMMON_PASSWORDS = {
    "password",
    "123456",
    "12345678",
    "qwerty",
    "admin",
    "letmein",
    "welcome",
    "abc123",
    "111111",
    "changeme",
}


@dataclass(frozen=True)
class PasswordPolicy:
    """Tham số chính sách mật khẩu (nạp từ config, không hardcode)."""

    min_length: int = 8
    require_upper: bool = True
    require_lower: bool = True
    require_digit: bool = True
    require_special: bool = True
    max_age_days: int = 90  # 0 = không hết hạn
    forbid_common: bool = True

    def to_dict(self) -> dict:
        return {
            "min_length": self.min_length,
            "require_upper": self.require_upper,
            "require_lower": self.require_lower,
            "require_digit": self.require_digit,
            "require_special": self.require_special,
            "max_age_days": self.max_age_days,
            "forbid_common": self.forbid_common,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordPolicy":
        valid = {k: v for k, v in (data or {}).items() if k in cls.__annotations__}
        return cls(**valid)


@dataclass
class PasswordValidation:
    """Kết quả kiểm tra mật khẩu."""

    valid: bool
    errors: List[str] = field(default_factory=list)


def validate_password(password: str, policy: PasswordPolicy) -> PasswordValidation:
    """Kiểm tra mật khẩu theo policy; trả về danh sách lỗi (nếu có)."""
    errors: List[str] = []
    if len(password) < policy.min_length:
        errors.append(f"Mật khẩu phải tối thiểu {policy.min_length} ký tự.")
    if policy.require_upper and not re.search(r"[A-Z]", password):
        errors.append("Mật khẩu phải có chữ hoa.")
    if policy.require_lower and not re.search(r"[a-z]", password):
        errors.append("Mật khẩu phải có chữ thường.")
    if policy.require_digit and not re.search(r"\d", password):
        errors.append("Mật khẩu phải có chữ số.")
    if policy.require_special and not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Mật khẩu phải có ký tự đặc biệt.")
    if policy.forbid_common and password.lower() in _COMMON_PASSWORDS:
        errors.append("Mật khẩu quá phổ biến, dễ đoán.")
    return PasswordValidation(valid=not errors, errors=errors)


def is_password_expired(
    changed_at: datetime | None, policy: PasswordPolicy, now: datetime | None = None
) -> bool:
    """Kiểm tra mật khẩu đã hết hạn theo max_age_days."""
    if policy.max_age_days <= 0 or changed_at is None:
        return False
    now = now or datetime.now(timezone.utc)
    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)
    return now - changed_at > timedelta(days=policy.max_age_days)
