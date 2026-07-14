"""
DTO — ModelInfo: thông tin model đang load.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List


@dataclass
class ModelInfo:
    """
    Metadata model đang được nạp trong Detection Engine.

    Attributes:
        name: Tên model.
        path: Đường dẫn weight.
        device: Thiết bị chạy (cpu/cuda:0).
        image_size: Kích thước input.
        half_precision: FP16 hay không.
        loaded: Đã load thành công chưa.
        warmup_done: Đã warmup chưa.
        loaded_at: Thời điểm load.
        class_labels: Nhãn logic được cấu hình.
    """

    name: str
    path: str
    device: str
    image_size: int
    half_precision: bool
    loaded: bool = False
    warmup_done: bool = False
    loaded_at: datetime | None = None
    class_labels: List[str] = field(default_factory=list)
    backend: str = "pytorch"

    def to_dict(self) -> dict[str, Any]:
        """Serialize cho API response."""
        return {
            "name": self.name,
            "path": self.path,
            "device": self.device,
            "image_size": self.image_size,
            "half_precision": self.half_precision,
            "backend": self.backend,
            "loaded": self.loaded,
            "warmup_done": self.warmup_done,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "class_labels": self.class_labels,
        }
