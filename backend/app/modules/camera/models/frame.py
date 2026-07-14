"""
Domain models in-memory — Frame packet cho pipeline stream.

Không phải SQLAlchemy ORM (ORM nằm ở app.models.camera).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np


@dataclass
class FramePacket:
    """
    Một frame đọc từ RTSP — metadata + raw BGR array.

    Attributes:
        camera_id: ID camera trong DB.
        frame_id: Số thứ tự frame tăng dần trong phiên worker.
        timestamp: Thời điểm capture (UTC).
        data: Mảng numpy BGR (H, W, 3) — chỉ dùng để buffer/encode, không phân tích AI.
        read_time_ms: Thời gian đọc từ stream (ms).
        decode_time_ms: Thời gian decode frame (ms).
    """

    camera_id: int
    frame_id: int
    timestamp: datetime
    data: np.ndarray
    read_time_ms: float = 0.0
    decode_time_ms: float = 0.0
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self) -> None:
        """Tính width/height từ shape numpy."""
        self.height, self.width = self.data.shape[:2]


@dataclass
class CameraRuntimeStatus:
    """
    Trạng thái runtime in-memory của một camera worker.

    Đồng bộ với HealthMonitor + FPSMonitor.
    """

    camera_id: int
    is_running: bool = False
    is_connected: bool = False
    status: str = "offline"
    reconnect_count: int = 0
    dropped_frames: int = 0
    current_fps: float = 0.0
    average_fps: float = 0.0
    latency_ms: float = 0.0
    queue_size: int = 0
    last_frame_at: datetime | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict cho API response."""
        return {
            "camera_id": self.camera_id,
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "status": self.status,
            "reconnect_count": self.reconnect_count,
            "dropped_frames": self.dropped_frames,
            "current_fps": round(self.current_fps, 2),
            "average_fps": round(self.average_fps, 2),
            "latency_ms": round(self.latency_ms, 2),
            "queue_size": self.queue_size,
            "last_frame_at": self.last_frame_at.isoformat() if self.last_frame_at else None,
            "last_error": self.last_error,
        }


def utc_now() -> datetime:
    """Trả về datetime UTC hiện tại."""
    return datetime.now(timezone.utc)
