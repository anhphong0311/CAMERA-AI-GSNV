"""
Load cấu hình tracking.yaml — không hardcode tham số tracking/ROI.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field


class TrackerConfig(BaseModel):
    """Tham số thuật toán tracking (ByteTrack)."""

    type: str = "bytetrack"
    track_thresh: float = Field(default=0.5, ge=0.0, le=1.0)
    new_track_thresh: float = Field(default=0.6, ge=0.0, le=1.0)
    low_thresh: float = Field(default=0.1, ge=0.0, le=1.0)
    match_thresh: float = Field(default=0.8, ge=0.0, le=1.0)
    track_buffer: int = Field(default=30, ge=1, le=1000)
    min_box_area: float = Field(default=100.0, ge=0.0)
    frame_rate: int = Field(default=30, ge=1, le=240)


class LifecycleConfig(BaseModel):
    """Vòng đời track."""

    max_lost_frames: int = Field(default=30, ge=1, le=1000)
    max_tracks: int = Field(default=300, ge=1, le=10000)


class MotionConfig(BaseModel):
    """Cấu hình phân tích chuyển động."""

    history_size: int = Field(default=60, ge=2, le=1000)
    stationary_speed: float = Field(default=2.0, ge=0.0)


class ROIRegionConfig(BaseModel):
    """Một vùng ROI cấu hình."""

    id: str
    name: str
    polygon: List[List[float]]
    color: str = "#3b82f6"
    description: str = ""


class ROIConfig(BaseModel):
    """Cấu hình ROI toàn cục + theo camera."""

    regions: List[ROIRegionConfig] = Field(default_factory=list)
    cameras: Dict[str, List[ROIRegionConfig]] = Field(default_factory=dict)

    def for_camera(self, camera_id: int) -> List[ROIRegionConfig]:
        """
        Lấy danh sách ROI áp cho camera.

        Ưu tiên override theo camera; nếu không có thì dùng regions toàn cục.
        """
        override = self.cameras.get(str(camera_id))
        if override:
            return override
        return self.regions


class TrackingConfig(BaseModel):
    """Schema tổng cấu hình Tracking Engine từ tracking.yaml."""

    tracker: TrackerConfig = Field(default_factory=TrackerConfig)
    lifecycle: LifecycleConfig = Field(default_factory=LifecycleConfig)
    motion: MotionConfig = Field(default_factory=MotionConfig)
    roi: ROIConfig = Field(default_factory=ROIConfig)


def _default_config_path() -> Path:
    """Tìm tracking.yaml — env TRACKING_CONFIG_PATH hoặc vị trí mặc định."""
    candidates: list[Path] = []
    env_path = os.getenv("TRACKING_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("/config/tracking.yaml"),
            Path("config/tracking.yaml"),
            Path(__file__).resolve().parents[5] / "config" / "tracking.yaml",
            Path(__file__).resolve().parents[4] / "config" / "tracking.yaml",
        ]
    )
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


@lru_cache
def load_tracking_config(path: str | None = None) -> TrackingConfig:
    """
    Đọc và parse tracking.yaml thành TrackingConfig.

    Args:
        path: Đường dẫn tùy chọn; mặc định tìm tự động.

    Returns:
        TrackingConfig đã validate.

    Raises:
        FileNotFoundError: Không tìm thấy file cấu hình.
    """
    config_path = Path(path) if path else _default_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Không tìm thấy tracking.yaml tại {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return TrackingConfig(**raw)
