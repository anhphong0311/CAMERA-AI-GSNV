"""
Image I/O — decode/encode ảnh cho Detection Engine (độc lập Camera Service).

Chỉ dùng cv2/numpy — không phân tích nội dung.
"""

from __future__ import annotations

import base64

import cv2
import numpy as np

from app.modules.ai.exceptions import InvalidFrameError


def decode_base64_image(image_base64: str) -> np.ndarray:
    """
    Giải mã chuỗi base64 (JPEG/PNG) thành ảnh BGR numpy.

    Chấp nhận cả data URI (data:image/jpeg;base64,...).

    Args:
        image_base64: Chuỗi base64.

    Returns:
        np.ndarray BGR (H,W,3).

    Raises:
        InvalidFrameError: Không decode được.
    """
    if not image_base64:
        raise InvalidFrameError("Chuỗi base64 rỗng.")
    payload = image_base64.split(",", 1)[1] if image_base64.startswith("data:") else image_base64
    try:
        raw = base64.b64decode(payload)
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as exc:
        raise InvalidFrameError(f"Lỗi decode base64: {exc}") from exc
    if frame is None:
        raise InvalidFrameError("Không decode được ảnh từ base64.")
    return frame


def encode_image_base64(frame: np.ndarray, quality: int = 85) -> str:
    """
    Encode ảnh BGR → chuỗi base64 JPEG.

    Args:
        frame: Ảnh BGR.
        quality: Chất lượng JPEG.

    Returns:
        str: Base64 (không prefix data URI).
    """
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise InvalidFrameError("Không encode được ảnh JPEG.")
    return base64.b64encode(buf.tobytes()).decode("ascii")
