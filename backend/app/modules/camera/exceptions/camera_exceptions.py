"""
Exception riêng cho Camera Service module.

Tách khỏi app.exceptions để module có thể tái sử dụng độc lập.
"""

from app.exceptions.base import AEMSException


class CameraException(AEMSException):
    """Lớc cơ sở cho lỗi camera module."""

    def __init__(self, message: str, code: str = "CAMERA_ERROR") -> None:
        super().__init__(message=message, code=code)


class CameraNotFoundError(CameraException):
    """Camera không tồn tại trong DB hoặc manager."""

    def __init__(self, camera_id: int) -> None:
        super().__init__(
            message=f"Camera id={camera_id} không tồn tại.",
            code="NOT_FOUND",
        )


class CameraAlreadyRunningError(CameraException):
    """Worker camera đang chạy."""

    def __init__(self, camera_id: int) -> None:
        super().__init__(
            message=f"Camera id={camera_id} đang chạy.",
            code="CONFLICT",
        )


class CameraNotRunningError(CameraException):
    """Worker camera chưa chạy."""

    def __init__(self, camera_id: int) -> None:
        super().__init__(
            message=f"Camera id={camera_id} chưa chạy.",
            code="CAMERA_NOT_RUNNING",
        )


class RTSPConnectionError(CameraException):
    """Không kết nối được RTSP stream."""

    def __init__(self, message: str = "Không kết nối được RTSP.") -> None:
        super().__init__(message=message, code="RTSP_CONNECTION_ERROR")


class FrameBufferEmptyError(CameraException):
    """Buffer không có frame."""

    def __init__(self) -> None:
        super().__init__(message="Không có frame trong buffer.", code="FRAME_BUFFER_EMPTY")
