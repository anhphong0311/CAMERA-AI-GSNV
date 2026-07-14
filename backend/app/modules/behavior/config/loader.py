"""
Load cấu hình behavior.yaml — không hardcode ngưỡng/tham số pose.
"""

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class PoseConfig(BaseModel):
    """Cấu hình pose model."""

    type: str = "yolo"
    model_path: str = "models/yolo11n-pose.pt"
    device: str = "auto"
    image_size: int = Field(default=640, ge=32, le=4096)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    keypoint_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    half_precision: bool = False
    warmup_iterations: int = Field(default=2, ge=0, le=50)
    auto_load: bool = True


class AssociatorConfig(BaseModel):
    """Cấu hình gán pose ↔ track."""

    iou_threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class ThresholdConfig(BaseModel):
    """Ngưỡng trích xuất đặc trưng."""

    head_side_ratio: float = 0.15
    head_down_ratio: float = 0.35
    head_up_ratio: float = -0.05
    head_stability_window: int = Field(default=15, ge=2, le=300)
    lean_forward_ratio: float = 0.15
    hand_near_face_ratio: float = 0.6
    hand_near_phone_px: float = 60.0
    food_near_mouth_ratio: float = 0.7
    standing_leg_ratio: float = 1.1
    stationary_speed: float = 2.0


class TemporalConfig(BaseModel):
    """Cấu hình temporal buffer."""

    buffer_size: int = Field(default=300, ge=2, le=5000)
    window: int = Field(default=30, ge=2, le=1000)
    max_tracks: int = Field(default=500, ge=1, le=10000)


class BehaviorConfig(BaseModel):
    """Schema tổng cấu hình Behavior Feature Engine."""

    pose: PoseConfig = Field(default_factory=PoseConfig)
    associator: AssociatorConfig = Field(default_factory=AssociatorConfig)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)
    frame_rate: int = Field(default=30, ge=1, le=240)


def _default_config_path() -> Path:
    """Tìm behavior.yaml — env BEHAVIOR_CONFIG_PATH hoặc vị trí mặc định."""
    candidates: list[Path] = []
    env_path = os.getenv("BEHAVIOR_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("/config/behavior.yaml"),
            Path("config/behavior.yaml"),
            Path(__file__).resolve().parents[5] / "config" / "behavior.yaml",
            Path(__file__).resolve().parents[4] / "config" / "behavior.yaml",
        ]
    )
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


@lru_cache
def load_behavior_config(path: str | None = None) -> BehaviorConfig:
    """
    Đọc và parse behavior.yaml thành BehaviorConfig.

    Args:
        path: Đường dẫn tùy chọn; mặc định tìm tự động.

    Returns:
        BehaviorConfig đã validate.

    Raises:
        FileNotFoundError: Không tìm thấy file cấu hình.
    """
    config_path = Path(path) if path else _default_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Không tìm thấy behavior.yaml tại {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return BehaviorConfig(**raw)
