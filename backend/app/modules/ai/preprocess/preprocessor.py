"""
ImagePreprocessor — chuẩn bị frame trước inference.

Cung cấp: validate, convert color, letterbox resize, normalize.
Chỉ xử lý ảnh — KHÔNG phân tích nội dung.

Backend Ultralytics tự làm letterbox nội bộ; các hàm ở đây phục vụ:
- Validate frame (bắt InvalidFrameError sớm).
- Đường inference "raw" cho backend ONNX/TensorRT sau này (không đổi business logic).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

from app.modules.ai.exceptions import InvalidFrameError


@dataclass(frozen=True)
class LetterboxMeta:
    """
    Metadata letterbox — dùng để map tọa độ ngược về ảnh gốc.

    Attributes:
        ratio: Tỉ lệ scale áp dụng.
        pad_w: Padding ngang (mỗi bên) tính bằng pixel.
        pad_h: Padding dọc (mỗi bên) tính bằng pixel.
        orig_w / orig_h: Kích thước ảnh gốc.
        new_w / new_h: Kích thước đích (letterbox square).
    """

    ratio: float
    pad_w: float
    pad_h: float
    orig_w: int
    orig_h: int
    new_w: int
    new_h: int


class ImagePreprocessor:
    """
    Bộ tiền xử lý ảnh cho Detection Engine.

    Stateless — an toàn dùng chung nhiều thread.
    """

    def __init__(self, image_size: int = 640) -> None:
        self._image_size = image_size

    @property
    def image_size(self) -> int:
        """Kích thước đích (vuông)."""
        return self._image_size

    def validate(self, frame: np.ndarray) -> None:
        """
        Kiểm tra frame hợp lệ.

        Args:
            frame: Mảng numpy BGR.

        Raises:
            InvalidFrameError: Frame None/sai shape/rỗng.
        """
        if frame is None:
            raise InvalidFrameError("Frame là None.")
        if not isinstance(frame, np.ndarray):
            raise InvalidFrameError("Frame không phải numpy array.")
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise InvalidFrameError(f"Frame phải có shape (H,W,3), nhận {frame.shape}.")
        if frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
            raise InvalidFrameError("Frame rỗng.")

    def bgr_to_rgb(self, frame: np.ndarray) -> np.ndarray:
        """Chuyển BGR (OpenCV) → RGB (model)."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def letterbox(
        self,
        frame: np.ndarray,
        color: Tuple[int, int, int] = (114, 114, 114),
    ) -> Tuple[np.ndarray, LetterboxMeta]:
        """
        Resize giữ tỉ lệ + padding về ảnh vuông image_size.

        Args:
            frame: Ảnh BGR gốc.
            color: Màu padding.

        Returns:
            Tuple (ảnh letterbox, LetterboxMeta) — meta để map tọa độ ngược.
        """
        self.validate(frame)
        orig_h, orig_w = frame.shape[:2]
        size = self._image_size

        ratio = min(size / orig_w, size / orig_h)
        new_unpad_w = int(round(orig_w * ratio))
        new_unpad_h = int(round(orig_h * ratio))

        resized = cv2.resize(
            frame, (new_unpad_w, new_unpad_h), interpolation=cv2.INTER_LINEAR
        )

        pad_w = (size - new_unpad_w) / 2.0
        pad_h = (size - new_unpad_h) / 2.0

        top = int(round(pad_h - 0.1))
        bottom = int(round(pad_h + 0.1))
        left = int(round(pad_w - 0.1))
        right = int(round(pad_w + 0.1))

        padded = cv2.copyMakeBorder(
            resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )
        meta = LetterboxMeta(
            ratio=ratio,
            pad_w=pad_w,
            pad_h=pad_h,
            orig_w=orig_w,
            orig_h=orig_h,
            new_w=size,
            new_h=size,
        )
        return padded, meta

    def normalize(self, frame: np.ndarray) -> np.ndarray:
        """
        Chuẩn hóa pixel về [0,1] float32 và chuyển sang CHW.

        Args:
            frame: Ảnh RGB uint8 (H,W,3).

        Returns:
            np.ndarray float32 (3,H,W).
        """
        arr = frame.astype(np.float32) / 255.0
        return np.transpose(arr, (2, 0, 1))

    def prepare(self, frame: np.ndarray) -> Tuple[np.ndarray, LetterboxMeta]:
        """
        Pipeline đầy đủ cho backend raw: validate → letterbox → RGB → normalize CHW.

        Args:
            frame: Ảnh BGR gốc.

        Returns:
            Tuple (tensor CHW float32, LetterboxMeta).
        """
        padded, meta = self.letterbox(frame)
        rgb = self.bgr_to_rgb(padded)
        tensor = self.normalize(rgb)
        return tensor, meta
