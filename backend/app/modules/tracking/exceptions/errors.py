"""
Exception hierarchy cho Tracking Engine.
"""

from app.exceptions.base import AEMSException


class TrackingException(AEMSException):
    """Lớp cơ sở cho lỗi Tracking Engine."""

    def __init__(self, message: str, code: str = "TRACKING_ERROR") -> None:
        super().__init__(message=message, code=code)


class TrackingLostError(TrackingException):
    """Track bị mất ngoài khả năng phục hồi."""

    def __init__(self, track_id: int) -> None:
        super().__init__(message=f"Track {track_id} bị mất.", code="TRACKING_LOST")


class InvalidDetectionError(TrackingException):
    """Dữ liệu detection đầu vào không hợp lệ."""

    def __init__(self, message: str = "DetectionResult không hợp lệ.") -> None:
        super().__init__(message=message, code="INVALID_DETECTION")


class ROIError(TrackingException):
    """Lỗi cấu hình/định nghĩa ROI (polygon không hợp lệ...)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="ROI_ERROR")


class TrackOverflowError(TrackingException):
    """Vượt số track tối đa cho một camera."""

    def __init__(self, camera_id: int, max_tracks: int) -> None:
        super().__init__(
            message=f"Camera {camera_id} vượt {max_tracks} track.",
            code="TRACK_OVERFLOW",
        )


class MemoryOverflowError(TrackingException):
    """Bộ nhớ tracking vượt ngưỡng an toàn."""

    def __init__(self, message: str = "Tràn bộ nhớ tracking.") -> None:
        super().__init__(message=message, code="MEMORY_OVERFLOW")
