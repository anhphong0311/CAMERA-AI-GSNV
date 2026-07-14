"""
Encode frame numpy → JPEG bytes/base64 cho API preview.

Chỉ encode — không phân tích nội dung.
"""

from __future__ import annotations

import base64
from typing import Optional, Tuple

import cv2
import numpy as np


def resize_for_preview(
    frame: np.ndarray,
    max_width: int = 960,
) -> np.ndarray:
    """Thu nhỏ frame preview nếu rộng hơn max_width (giữ tỉ lệ)."""
    if max_width <= 0:
        return frame
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    scale = max_width / float(w)
    nh = max(1, int(round(h * scale)))
    return cv2.resize(frame, (max_width, nh), interpolation=cv2.INTER_AREA)


def encode_frame_jpeg(
    frame: np.ndarray,
    quality: int = 85,
    max_width: int = 0,
) -> Tuple[bytes, int, int]:
    """
    Encode BGR frame thành JPEG.

    Args:
        frame: Mảng numpy BGR.
        quality: Chất lượng JPEG 0-100.
        max_width: Thu nhỏ preview nếu > 0.

    Returns:
        Tuple (jpeg_bytes, width, height).
    """
    if max_width > 0:
        frame = resize_for_preview(frame, max_width)
    h, w = frame.shape[:2]
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("Không encode được frame JPEG.")
    return buf.tobytes(), w, h


def encode_frame_base64(
    frame: np.ndarray,
    quality: int = 85,
    max_width: int = 0,
) -> str:
    """
    Encode frame thành chuỗi base64.

    Args:
        frame: BGR numpy array.
        quality: JPEG quality.
        max_width: Thu nhỏ preview nếu > 0.

    Returns:
        str: Base64 string (không có data URI prefix).
    """
    jpeg_bytes, _, _ = encode_frame_jpeg(frame, quality, max_width=max_width)
    return base64.b64encode(jpeg_bytes).decode("ascii")
