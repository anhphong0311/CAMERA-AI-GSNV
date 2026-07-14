"""
Exception hierarchy cho Event Processing Center.
"""

from app.exceptions.base import AEMSException


class EventProcessingException(AEMSException):
    """Lớp cơ sở cho lỗi Event Processing."""

    def __init__(self, message: str, code: str = "EVENT_PROCESSING_ERROR") -> None:
        super().__init__(message=message, code=code)


class InvalidEventError(EventProcessingException):
    """Event không hợp lệ (thiếu trường bắt buộc)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_EVENT")


class EventNotFoundError(EventProcessingException):
    """Không tìm thấy event record."""

    def __init__(self, event_id: str) -> None:
        super().__init__(message=f"Không tìm thấy event: {event_id}", code="EVENT_NOT_FOUND")


class SnapshotError(EventProcessingException):
    """Lỗi tạo snapshot."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="SNAPSHOT_ERROR")


class RecorderError(EventProcessingException):
    """Lỗi ghi video evidence."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="RECORDER_ERROR")


class NotificationError(EventProcessingException):
    """Lỗi gửi notification."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="NOTIFICATION_ERROR")


class TelegramError(NotificationError):
    """Lỗi gửi Telegram (timeout/network)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message)
        self.code = "TELEGRAM_ERROR"


class DiskFullError(EventProcessingException):
    """Hết dung lượng lưu evidence."""

    def __init__(self, message: str = "Hết dung lượng ổ đĩa.") -> None:
        super().__init__(message=message, code="DISK_FULL")
