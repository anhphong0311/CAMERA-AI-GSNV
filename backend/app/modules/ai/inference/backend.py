"""
Backend inference — abstraction cho phép đổi Ultralytics → ONNX → TensorRT
mà KHÔNG sửa business logic (Dependency Inversion Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

import numpy as np

from app.modules.ai.models import RawDetection


class InferenceBackend(ABC):
    """
    Interface backend inference.

    Concrete: UltralyticsBackend (Sprint 3); ONNXBackend/TensorRTBackend (sau).
    """

    @property
    @abstractmethod
    def device(self) -> str:
        """Thiết bị đang chạy."""

    @property
    @abstractmethod
    def class_names(self) -> dict[int, str]:
        """Map COCO id → tên class gốc của model."""

    @abstractmethod
    def predict(
        self,
        frame: np.ndarray,
        image_size: int,
        confidence: float,
        iou: float,
        allowed_class_ids: Sequence[int],
        half: bool,
    ) -> List[RawDetection]:
        """
        Chạy inference trên một frame.

        Args:
            frame: Ảnh BGR gốc.
            image_size: Kích thước input.
            confidence: Ngưỡng confidence tối thiểu.
            iou: Ngưỡng IoU NMS.
            allowed_class_ids: Chỉ detect các class này.
            half: FP16.

        Returns:
            List[RawDetection] ở tọa độ ảnh gốc.
        """

    @abstractmethod
    def warmup(self, image_size: int, iterations: int = 3) -> None:
        """Chạy vài inference giả để nạp CUDA kernel / cache."""

    @abstractmethod
    def release(self) -> None:
        """Giải phóng tài nguyên model."""


class UltralyticsBackend(InferenceBackend):
    """
    Backend dùng Ultralytics YOLO11.

    Ultralytics tự letterbox + NMS + map tọa độ về ảnh gốc.
    Lazy import ultralytics/torch để module import được khi chưa cài.
    """

    def __init__(self, model_path: str, device: str, half: bool) -> None:
        self._model_path = model_path
        self._device = device
        self._half = half
        self._model = None  # ultralytics.YOLO — nạp trong load()

    def load(self) -> None:
        """
        Nạp model YOLO từ weight.

        Raises:
            ModelLoadError: Thiếu ultralytics hoặc lỗi nạp.
        """
        from app.modules.ai.exceptions import ModelLoadError

        try:
            from ultralytics import YOLO
        except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
            raise ModelLoadError(
                f"Chưa cài đặt ultralytics/torch: {exc}"
            ) from exc

        try:
            model = YOLO(self._model_path)
            model.to(self._device)
            self._model = model
        except Exception as exc:  # pragma: no cover
            raise ModelLoadError(f"Lỗi nạp model: {exc}") from exc

    @property
    def device(self) -> str:
        """Thiết bị đang chạy."""
        return self._device

    @property
    def class_names(self) -> dict[int, str]:
        """Map id → tên class từ model (COCO)."""
        if self._model is None:
            return {}
        names = getattr(self._model, "names", {})
        return dict(names)

    def predict(
        self,
        frame: np.ndarray,
        image_size: int,
        confidence: float,
        iou: float,
        allowed_class_ids: Sequence[int],
        half: bool,
    ) -> List[RawDetection]:
        """Chạy predict và parse kết quả thành RawDetection."""
        from app.modules.ai.exceptions import (
            CUDAError,
            GPUOutOfMemoryError,
            InferenceError,
            ModelNotLoadedError,
        )

        if self._model is None:
            raise ModelNotLoadedError()

        try:
            results = self._model.predict(
                source=frame,
                imgsz=image_size,
                conf=confidence,
                iou=iou,
                classes=list(allowed_class_ids) or None,
                half=half,
                device=self._device,
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover - phụ thuộc GPU
            message = str(exc).lower()
            if "out of memory" in message or "cuda out of memory" in message:
                raise GPUOutOfMemoryError(str(exc)) from exc
            if "cuda" in message:
                raise CUDAError(str(exc)) from exc
            raise InferenceError(str(exc)) from exc

        return self._parse_results(results)

    @staticmethod
    def _parse_results(results) -> List[RawDetection]:
        """Chuyển ultralytics Results → List[RawDetection]."""
        raws: List[RawDetection] = []
        if not results:
            return raws
        boxes = getattr(results[0], "boxes", None)
        if boxes is None:
            return raws
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            raws.append(
                RawDetection(
                    class_id=cls_id,
                    confidence=conf,
                    xyxy=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                )
            )
        return raws

    def warmup(self, image_size: int, iterations: int = 3) -> None:
        """Chạy inference trên ảnh đen để nạp kernel."""
        if self._model is None:
            return
        dummy = np.zeros((image_size, image_size, 3), dtype=np.uint8)
        for _ in range(max(0, iterations)):
            self._model.predict(
                source=dummy,
                imgsz=image_size,
                device=self._device,
                half=self._half,
                verbose=False,
            )

    def release(self) -> None:
        """Giải phóng model + giải phóng VRAM nếu dùng CUDA."""
        self._model = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # pragma: no cover
            pass
