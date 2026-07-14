"""Configuration Center Service (Sprint 9) — cấu hình lưu DB, không hardcode."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.modules.admin.repositories.base import ConfigRepository
from app.modules.admin.repositories.entities import ConfigEntity
from app.modules.admin.security.password_policy import PasswordPolicy

# Các section được quản lý (Configuration Center)
CONFIG_SECTIONS = [
    "telegram",
    "camera",
    "detection",
    "tracking",
    "behavior",
    "rule",
    "gpu",
    "storage",
    "retention",
    "backup",
    "scheduler",
    "security",
    "system",
]

# Giá trị mặc định khi DB chưa có (seed lần đầu). Không dùng làm hardcode runtime —
# chỉ là default có thể override hoàn toàn qua API/DB.
DEFAULT_CONFIG: Dict[str, Any] = {
    "system.company_name": "AEMS",
    "system.office_name": "HQ",
    "system.timezone": "Asia/Ho_Chi_Minh",
    "system.language": "vi",
    "storage.video_path": "./data/videos",
    "storage.snapshot_path": "./data/snapshots",
    "storage.backup_path": "./data/backups",
    "retention.video_days": 30,
    "retention.snapshot_days": 30,
    "retention.event_days": 90,
    "retention.log_days": 30,
    "security.session_timeout_minutes": 60,
    "security.rate_limit_per_minute": 120,
    "security.password_policy": PasswordPolicy().to_dict(),
    "scheduler.daily_cleanup_hour": 3,
    "backup.auto_enabled": True,
    "backup.interval_seconds": 86400,
}


class ConfigService:
    """Quản lý cấu hình hệ thống dạng section.key = value."""

    def __init__(self, repo: ConfigRepository) -> None:
        self._repo = repo

    def seed_defaults(self) -> None:
        """Nạp giá trị mặc định nếu key chưa tồn tại."""
        for key, value in DEFAULT_CONFIG.items():
            if self._repo.get(key) is None:
                section = key.split(".", 1)[0]
                self._repo.set(
                    ConfigEntity(section=section, key=key, value=value, updated_by="system")
                )

    def all(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._repo.all()]

    def get_section(self, section: str) -> Dict[str, Any]:
        return {c.key: c.value for c in self._repo.section(section)}

    def get_value(self, key: str, default: Any = None) -> Any:
        entry = self._repo.get(key)
        return entry.value if entry is not None else default

    def set_value(
        self, key: str, value: Any, updated_by: Optional[str] = None
    ) -> ConfigEntity:
        section = key.split(".", 1)[0]
        return self._repo.set(
            ConfigEntity(section=section, key=key, value=value, updated_by=updated_by)
        )

    def delete(self, key: str) -> bool:
        return self._repo.delete(key)

    def password_policy(self) -> PasswordPolicy:
        data = self.get_value("security.password_policy")
        if isinstance(data, dict):
            return PasswordPolicy.from_dict(data)
        return PasswordPolicy()

    def session_timeout_minutes(self) -> int:
        return int(self.get_value("security.session_timeout_minutes", 60) or 60)

    def rate_limit_per_minute(self) -> int:
        return int(self.get_value("security.rate_limit_per_minute", 120) or 120)
