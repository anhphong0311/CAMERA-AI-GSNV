"""
DTO — RawDetection: đầu ra thô từ inference backend (trước postprocess).

Tọa độ theo pixel gốc của frame (backend đã map về ảnh gốc).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RawDetection:
    """
    Detection thô từ backend inference.

    Attributes:
        class_id: COCO class id.
        confidence: Độ tin cậy 0-1.
        xyxy: Tọa độ (x1,y1,x2,y2) pixel gốc.
    """

    class_id: int
    confidence: float
    xyxy: Tuple[float, float, float, float]
