"""
Load cấu hình detection.yaml — không hardcode tham số inference.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field


class ClassConfig(BaseModel):
    """
    Cấu hình một nhãn logic cần detect.

    Attributes:
        ids: Danh sách COCO class id gộp vào nhãn này (food gom nhiều id).
        confidence: Ngưỡng confidence riêng cho nhãn.
    """

    ids: List[int]
    confidence: float = Field(ge=0.0, le=1.0)


class ModelConfig(BaseModel):
    """Thông tin weight model."""

    path: str
    name: str


class QueueConfig(BaseModel):
    """Cấu hình hàng đợi multi-camera."""

    max_size: int = Field(default=5, ge=1, le=100)
    num_workers: int = Field(default=2, ge=1, le=32)
    poll_interval_ms: int = Field(default=5, ge=1, le=1000)


class DetectionConfig(BaseModel):
    """
    Schema tổng cấu hình Detection Engine từ detection.yaml.

    Tách khỏi code để đổi model/ngưỡng không cần sửa business logic.
    """

    model: ModelConfig
    device: str = "auto"
    half_precision: bool = False
    image_size: int = Field(default=640, ge=32, le=4096)
    nms_iou: float = Field(default=0.45, ge=0.0, le=1.0)
    batch_size: int = Field(default=1, ge=1, le=64)
    max_detections: int = Field(default=100, ge=1, le=1000)
    default_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    auto_load: bool = True
    warmup_iterations: int = Field(default=3, ge=0, le=50)
    classes: Dict[str, ClassConfig]
    queue: QueueConfig = Field(default_factory=QueueConfig)

    def build_class_map(self) -> Dict[int, tuple[str, float]]:
        """
        Tạo map COCO id → (nhãn logic, ngưỡng confidence).

        Dùng cho postprocess: đổi tên class + áp ngưỡng riêng.

        Returns:
            dict: {coco_id: (label, confidence_threshold)}
        """
        mapping: Dict[int, tuple[str, float]] = {}
        for label, cfg in self.classes.items():
            for coco_id in cfg.ids:
                mapping[coco_id] = (label, cfg.confidence)
        return mapping

    def allowed_class_ids(self) -> List[int]:
        """Danh sách COCO id được phép — truyền vào model để giảm chi phí."""
        return sorted(self.build_class_map().keys())

    def min_confidence(self) -> float:
        """
        Ngưỡng confidence nhỏ nhất trong tất cả class.

        Model chạy ở ngưỡng này; postprocess lọc lại theo từng class.

        Returns:
            float: min confidence.
        """
        if not self.classes:
            return self.default_confidence
        return min(c.confidence for c in self.classes.values())


def _default_config_path() -> Path:
    """Tìm detection.yaml — env DETECTION_CONFIG_PATH hoặc vị trí mặc định."""
    candidates: list[Path] = []
    env_path = os.getenv("DETECTION_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("/config/detection.yaml"),
            Path("config/detection.yaml"),
            Path(__file__).resolve().parents[5] / "config" / "detection.yaml",
            Path(__file__).resolve().parents[4] / "config" / "detection.yaml",
        ]
    )
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


@lru_cache
def load_detection_config(path: str | None = None) -> DetectionConfig:
    """
    Đọc và parse detection.yaml thành DetectionConfig.

    Args:
        path: Đường dẫn tùy chọn; mặc định tìm tự động.

    Returns:
        DetectionConfig: Cấu hình đã validate.

    Raises:
        FileNotFoundError: Không tìm thấy file cấu hình.
    """
    config_path = Path(path) if path else _default_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Không tìm thấy detection.yaml tại {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return DetectionConfig(**raw)
