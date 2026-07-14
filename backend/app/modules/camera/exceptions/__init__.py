"""Camera module exceptions."""

from app.modules.camera.exceptions.camera_exceptions import (
    CameraAlreadyRunningError,
    CameraException,
    CameraNotFoundError,
    CameraNotRunningError,
    FrameBufferEmptyError,
    RTSPConnectionError,
)

__all__ = [
    "CameraException",
    "CameraNotFoundError",
    "CameraAlreadyRunningError",
    "CameraNotRunningError",
    "RTSPConnectionError",
    "FrameBufferEmptyError",
]
