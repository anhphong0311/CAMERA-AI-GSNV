"""
ProviderRegistry — đăng ký các kênh notification.

Cho phép thêm kênh mới (Email/Slack/Teams/Discord) mà không sửa business logic.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.modules.event.notification.provider import NotificationProvider


class ProviderRegistry:
    """Registry provider theo tên kênh."""

    def __init__(self) -> None:
        self._providers: Dict[str, NotificationProvider] = {}

    def register(self, provider: NotificationProvider) -> None:
        """Đăng ký một provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[NotificationProvider]:
        """Lấy provider theo tên kênh."""
        return self._providers.get(name)

    def names(self) -> List[str]:
        """Danh sách kênh đã đăng ký."""
        return list(self._providers.keys())

    def ready_names(self) -> List[str]:
        """Kênh đã sẵn sàng gửi."""
        return [n for n, p in self._providers.items() if p.is_ready]
