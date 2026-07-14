"""
ModelLoader — quản lý vòng đời model.

Chức năng: load, verify, warmup, reload, get_info, release.
Thread-safe. Lazy import backend nặng.
"""

from __future__ import annotations

import threading
from typing import Optional

from loguru import logger

from app.modules.ai.exceptions import ModelNotFoundError
from app.modules.ai.inference.backend import InferenceBackend, UltralyticsBackend
from app.modules.ai.models import ModelInfo, utc_now
from app.modules.ai.repositories.model_repository import ModelRepository
from app.modules.ai.utils.device import resolve_device


class ModelLoader:
    """
    Nạp và quản lý một model inference.

    Attributes:
        model_path: Đường dẫn weight.
        model_name: Tên hiển thị.
        image_size: Kích thước input.
    """

    def __init__(
        self,
        model_path: str,
        model_name: str,
        device: str = "auto",
        half_precision: bool = False,
        image_size: int = 640,
        class_labels: Optional[list[str]] = None,
        repository: Optional[ModelRepository] = None,
        backend_type: str = "pytorch",
        onnx_path: str = "",
        tensorrt_path: str = "",
        auto_export_onnx: bool = False,
    ) -> None:
        self.model_path = model_path
        self.model_name = model_name
        self._requested_device = device
        self._device = resolve_device(device)
        self._half = half_precision and self._device.startswith("cuda")
        self.image_size = image_size
        self._class_labels = class_labels or []
        self._repo = repository or ModelRepository()
        self._backend_type = backend_type
        self._onnx_path = onnx_path or model_path.replace(".pt", ".onnx")
        self._tensorrt_path = tensorrt_path or model_path.replace(".pt", ".engine")
        self._auto_export_onnx = auto_export_onnx
        self._backend: Optional[InferenceBackend] = None
        self._info = ModelInfo(
            name=model_name,
            path=model_path,
            device=self._device,
            image_size=image_size,
            half_precision=self._half,
            class_labels=self._class_labels,
        )
        self._lock = threading.RLock()

    @property
    def backend(self) -> Optional[InferenceBackend]:
        """Backend inference đã nạp (None nếu chưa load)."""
        return self._backend

    @property
    def is_loaded(self) -> bool:
        """Model đã load chưa."""
        return self._backend is not None

    def verify(self) -> None:
        """
        Kiểm tra weight tồn tại trước khi load.

        Raises:
            ModelNotFoundError: Không tìm thấy file weight.
        """
        if not self._repo.exists(self.model_path):
            raise ModelNotFoundError(self.model_path)

    def load(self, warmup_iterations: int = 3) -> ModelInfo:
        """
        Load model + verify + warmup.

        Args:
            warmup_iterations: Số vòng warmup.

        Returns:
            ModelInfo: Thông tin model sau khi load.
        """
        with self._lock:
            self.verify()
            logger.info(
                "Model loading | name={} path={} device={} backend={}",
                self.model_name,
                self.model_path,
                self._device,
                self._backend_type,
            )
            if self._backend_type == "pytorch":
                backend = UltralyticsBackend(
                    model_path=self._repo.resolve(self.model_path),
                    device=self._device,
                    half=self._half,
                )
                backend.load()
            else:
                from app.modules.performance.backends.factory import create_backend

                backend = create_backend(
                    self._backend_type,  # type: ignore[arg-type]
                    model_path=self._repo.resolve(self.model_path),
                    onnx_path=self._onnx_path,
                    tensorrt_path=self._tensorrt_path,
                    device=self._device,
                    half=self._half,
                    auto_export_onnx=self._auto_export_onnx,
                    image_size=self.image_size,
                )
            self._backend = backend
            self._info.backend = self._backend_type
            self._info.loaded = True
            self._info.loaded_at = utc_now()
            logger.info("Model loaded | name={}", self.model_name)

            if warmup_iterations > 0:
                self.warmup(warmup_iterations)
            return self._info

    def warmup(self, iterations: int = 3) -> None:
        """
        Warmup model để ổn định latency inference đầu tiên.

        Args:
            iterations: Số vòng warmup.
        """
        with self._lock:
            if self._backend is None:
                return
            logger.info("Model warmup | name={} iters={}", self.model_name, iterations)
            self._backend.warmup(self.image_size, iterations)
            self._info.warmup_done = True
            logger.info("Model warmup done | name={}", self.model_name)

    def reload(self, warmup_iterations: int = 3) -> ModelInfo:
        """
        Reload model — release rồi load lại (đổi weight khi cần).

        Returns:
            ModelInfo mới.
        """
        with self._lock:
            logger.info("Model reloading | name={}", self.model_name)
            self.release()
            self._device = resolve_device(self._requested_device)
            self._half = self._info.half_precision and self._device.startswith("cuda")
            self._info = ModelInfo(
                name=self.model_name,
                path=self.model_path,
                device=self._device,
                image_size=self.image_size,
                half_precision=self._half,
                class_labels=self._class_labels,
            )
            return self.load(warmup_iterations)

    def get_info(self) -> ModelInfo:
        """Trả về ModelInfo hiện tại."""
        with self._lock:
            return self._info

    def release(self) -> None:
        """Giải phóng model và VRAM."""
        with self._lock:
            if self._backend is not None:
                self._backend.release()
                self._backend = None
            self._info.loaded = False
            self._info.warmup_done = False
            logger.info("Model released | name={}", self.model_name)
