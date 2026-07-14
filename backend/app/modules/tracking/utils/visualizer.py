"""
Visualizer — vẽ overlay tracking để DEBUG.

Vẽ: track id, bbox, ROI polygon, center point, motion path, mũi tên hướng,
thời gian ở ROI. Chỉ dùng debug — không thuộc luồng nghiệp vụ.
"""

from __future__ import annotations

import math
from typing import Optional

import cv2
import numpy as np

from app.modules.tracking.models import TrackingResult
from app.modules.tracking.roi.roi_manager import ROIManager


def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """Chuyển '#rrggbb' → (b, g, r)."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (255, 0, 0)
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (b, g, r)


def _id_color(track_id: int) -> tuple[int, int, int]:
    """Sinh màu ổn định theo track id."""
    rng = (track_id * 2654435761) & 0xFFFFFFFF
    return (int(rng % 256), int((rng >> 8) % 256), int((rng >> 16) % 256))


def draw_tracks(
    frame: np.ndarray,
    result: TrackingResult,
    roi_manager: Optional[ROIManager] = None,
    camera_name: Optional[str] = None,
) -> np.ndarray:
    """
    Vẽ overlay tracking lên bản sao của frame.

    Args:
        frame: Ảnh BGR gốc.
        result: TrackingResult cần vẽ.
        roi_manager: ROIManager để vẽ polygon ROI (tùy chọn).
        camera_name: Tên camera hiển thị.

    Returns:
        np.ndarray: Ảnh mới đã vẽ.
    """
    canvas = frame.copy()

    # Vẽ ROI
    if roi_manager is not None:
        for roi in roi_manager.regions:
            if len(roi.polygon) >= 3:
                pts = np.array(roi.polygon, dtype=np.int32).reshape(-1, 1, 2)
                color = _hex_to_bgr(roi.color)
                cv2.polylines(canvas, [pts], isClosed=True, color=color, thickness=2)
                cv2.putText(
                    canvas,
                    roi.name,
                    (int(roi.polygon[0][0]) + 4, int(roi.polygon[0][1]) + 18),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                    cv2.LINE_AA,
                )

    for track in result.tracks:
        color = _id_color(track.track_id)
        x1, y1, x2, y2 = (int(v) for v in track.bbox)
        cx, cy = (int(v) for v in track.center)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

        label = f"ID {track.track_id} | {track.duration:.0f}s"
        if track.current_roi_name:
            label += f" | {track.current_roi_name}"
        cv2.putText(
            canvas,
            label,
            (x1, max(12, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
            cv2.LINE_AA,
        )

        # Center point
        cv2.circle(canvas, (cx, cy), 3, color, -1)

        # Motion path
        path = track.timeline.path()
        if len(path) >= 2:
            pts = np.array(path, dtype=np.int32).reshape(-1, 1, 2)
            cv2.polylines(canvas, [pts], isClosed=False, color=color, thickness=1)

        # Direction arrow
        vx, vy = track.velocity
        if math.hypot(vx, vy) > 0.5:
            scale = 6.0
            end = (int(cx + vx * scale), int(cy + vy * scale))
            cv2.arrowedLine(canvas, (cx, cy), end, color, 2, tipLength=0.3)

    header_parts = []
    if camera_name:
        header_parts.append(camera_name)
    header_parts.append(f"tracks: {result.count}")
    header_parts.append(result.timestamp.strftime("%H:%M:%S"))
    cv2.putText(
        canvas,
        " | ".join(header_parts),
        (8, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return canvas
