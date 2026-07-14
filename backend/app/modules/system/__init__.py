"""System control — bật/tắt toàn bộ giám sát qua Telegram / API."""

from app.modules.system.control import SystemControlService, init_system_control

__all__ = ["SystemControlService", "init_system_control"]
