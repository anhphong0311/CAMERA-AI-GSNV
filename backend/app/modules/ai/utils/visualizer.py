"""
Visualizer — vẽ bounding box lên frame để DEBUG.

CHỈ dùng để debug/kiểm thử — không thuộc luồng nghiệp vụ.
Vẽ: box, class, confidence, FPS, tên camera, timestamp.
"""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np

from app.modules.ai.models import DetectionResult

# Bảng màu cố định theo class (BGR) — đủ 10 class Sprint 3
_CLASS_COLORS = {
    "person": (0, 255, 0),
    "phone": (0, 0, 255),
    "cup": (255, 200, 0),
    "bottle": (255, 128, 0),
    "food": (0, 165, 255),
    "laptop": (255, 0, 255),
    "keyboard": (200, 200, 0),
    "mouse": (128, 0, 255),
    "chair": (128, 128, 128),
    "monitor": (255, 255, 0),
}
_DEFAULT_COLOR = (0, 255, 255)


def _color_for(label: str) -> Tuple[int, int, int]:
    """Màu vẽ cho một class."""
    return _CLASS_COLORS.get(label, _DEFAULT_COLOR)


def draw_detections(
    frame: np.ndarray,
    result: DetectionResult,
    camera_name: Optional[str] = None,
) -> np.ndarray:
    """
    Vẽ overlay bounding box + metadata lên bản sao của frame.

    Args:
        frame: Ảnh BGR gốc.
        result: DetectionResult cần vẽ.
        camera_name: Tên camera hiển thị (tùy chọn).

    Returns:
        np.ndarray: Ảnh mới đã vẽ (không sửa ảnh gốc).
    """
    canvas = frame.copy()

    for det in result.objects:
        x1, y1, x2, y2 = (int(v) for v in det.bbox.to_xyxy())
        color = _color_for(det.class_name)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(canvas, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            canvas,
            label,
            (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    # Thanh thông tin phía trên
    header_parts = []
    if camera_name:
        header_parts.append(camera_name)
    header_parts.append(f"FPS: {result.fps:.1f}")
    header_parts.append(f"obj: {result.count}")
    header_parts.append(result.timestamp.strftime("%H:%M:%S"))
    header = " | ".join(header_parts)
    cv2.putText(
        canvas,
        header,
        (8, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return canvas
