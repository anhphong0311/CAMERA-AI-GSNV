"""
Load cấu hình camera.yaml — không hardcode tham số stream.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class CameraStreamConfig(BaseModel):
    """
    Schema cấu hình stream từ camera.yaml.

    Mọi worker dùng chung config mặc định; có thể override per-camera sau này.
    """

    reconnect_delays: List[int] = Field(default=[1, 3, 5, 10, 30])
    queue_size: int = Field(default=30, ge=1, le=500)
    target_fps: int = Field(default=15, ge=1, le=60)
    buffer_size: int = Field(default=120, ge=10)
    frame_width: int = Field(default=0, ge=0)
    frame_height: int = Field(default=0, ge=0)
    timeout_seconds: int = Field(default=10, ge=1)
    auto_start_enabled: bool = True
    heartbeat_interval_seconds: int = Field(default=5, ge=1)
    # Preview live view (API /frame) — nhẹ hơn full-res
    preview_jpeg_quality: int = Field(default=60, ge=10, le=100)
    preview_max_width: int = Field(default=960, ge=0)


def _default_config_path() -> Path:
    """Tìm camera.yaml — env CAMERA_CONFIG_PATH hoặc các vị trí mặc định."""
    import os

    candidates: list[Path] = []
    env_path = os.getenv("CAMERA_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("/config/camera.yaml"),
            Path("config/camera.yaml"),
            Path(__file__).resolve().parents[5] / "config" / "camera.yaml",
            Path(__file__).resolve().parents[4] / "config" / "camera.yaml",
        ]
    )
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


@lru_cache
def load_camera_config(path: str | None = None) -> CameraStreamConfig:
    """
    Đọc và parse camera.yaml thành CameraStreamConfig.

    Args:
        path: Đường dẫn tùy chọn; mặc định tìm tự động.

    Returns:
        CameraStreamConfig: Cấu hình đã validate.
    """
    config_path = Path(path) if path else _default_config_path()
    if not config_path.exists():
        return CameraStreamConfig()
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return CameraStreamConfig(**raw)
