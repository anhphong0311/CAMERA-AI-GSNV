"""Camera API schemas."""

from app.modules.camera.schemas.camera import (
    CameraCreate,
    CameraFPSRead,
    CameraFrameRead,
    CameraHealthRead,
    CameraRead,
    CameraUpdate,
)

__all__ = [
    "CameraCreate",
    "CameraUpdate",
    "CameraRead",
    "CameraHealthRead",
    "CameraFPSRead",
    "CameraFrameRead",
]
