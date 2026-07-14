"""
TensorRT backend — Sprint 10.

Ưu tiên TensorRT engine (.engine); fallback ONNX Runtime TensorRT EP;
cuối cùng fallback ONNX CPU. Không đổi business logic.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from app.modules.ai.inference.backend import InferenceBackend
from app.modules.ai.models import RawDetection
from app.modules.performance.backends.onnx_backend import ONNXBackend, _COCO_NAMES


class TensorRTBackend(InferenceBackend):
    """
    Backend TensorRT — wrap engine hoặc ONNX+TRT EP.

    Nếu file .engine không tồn tại, thử dùng ONNX với TensorrtExecutionProvider.
    """

    def __init__(
        self,
        engine_path: str,
        onnx_path: str,
        device: str = "cuda:0",
        half: bool = True,
        class_names: dict[int, str] | None = None,
    ) -> None:
        self._engine_path = engine_path
        self._onnx_path = onnx_path
        self._device = device
        self._half = half
        self._class_names = class_names or dict(_COCO_NAMES)
        self._delegate: InferenceBackend | None = None
        self._mode = "none"

    def load(self) -> None:
        from pathlib import Path

        from app.modules.ai.exceptions import ModelLoadError

        engine = Path(self._engine_path)
        onnx = Path(self._onnx_path)

        # Thử TensorRT native engine qua onnxruntime TRT EP (engine serialized)
        if engine.exists():
            self._load_trt_engine()
            return

        if onnx.exists():
            self._load_trt_ep(onnx)
            return

        raise ModelLoadError(
            f"Không tìm thấy TensorRT engine ({self._engine_path}) hoặc ONNX ({self._onnx_path})"
        )

    def _load_trt_engine(self) -> None:
        from app.modules.ai.exceptions import ModelLoadError

        try:
            import onnxruntime as ort
            from pathlib import Path as P
        except ImportError as exc:
            raise ModelLoadError(f"onnxruntime cần cho TensorRT: {exc}") from exc

        device_id = int(self._device.split(":")[-1] if ":" in self._device else 0)
        cache_dir = str(P(self._engine_path).parent)
        onnx_file = self._onnx_path if P(self._onnx_path).exists() else self._engine_path
        providers = [
            (
                "TensorrtExecutionProvider",
                {
                    "device_id": device_id,
                    "trt_engine_cache_enable": True,
                    "trt_engine_cache_path": cache_dir,
                    "trt_fp16_enable": self._half,
                },
            ),
            ("CUDAExecutionProvider", {"device_id": device_id}),
            "CPUExecutionProvider",
        ]
        try:
            session = ort.InferenceSession(onnx_file, providers=providers)
            delegate = ONNXBackend(onnx_file, self._device, self._half, self._class_names)
            delegate._session = session  # type: ignore[attr-defined]
            delegate._input_name = session.get_inputs()[0].name
            self._delegate = delegate
            self._mode = "tensorrt_ep"
        except Exception as exc:
            raise ModelLoadError(f"TensorRT EP load failed: {exc}") from exc

    def _load_trt_ep(self, onnx_path) -> None:
        from app.modules.ai.exceptions import ModelLoadError

        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ModelLoadError(f"onnxruntime chưa cài: {exc}") from exc

        device_id = int(self._device.split(":")[-1] if ":" in self._device else 0)
        providers = [
            (
                "TensorrtExecutionProvider",
                {"device_id": device_id, "trt_fp16_enable": self._half},
            ),
            ("CUDAExecutionProvider", {"device_id": device_id}),
            "CPUExecutionProvider",
        ]
        try:
            delegate = ONNXBackend(str(onnx_path), self._device, self._half, self._class_names)
            delegate._session = ort.InferenceSession(str(onnx_path), providers=providers)
            delegate._input_name = delegate._session.get_inputs()[0].name
            self._delegate = delegate
            self._mode = "tensorrt_onnx"
        except Exception as exc:
            # Fallback pure ONNX CUDA
            delegate = ONNXBackend(str(onnx_path), self._device, self._half, self._class_names)
            delegate.load()
            self._delegate = delegate
            self._mode = "onnx_fallback"

    @property
    def device(self) -> str:
        return self._device

    @property
    def class_names(self) -> dict[int, str]:
        return self._class_names

    @property
    def runtime_mode(self) -> str:
        return self._mode

    def predict(
        self,
        frame: np.ndarray,
        image_size: int,
        confidence: float,
        iou: float,
        allowed_class_ids: Sequence[int],
        half: bool,
    ) -> List[RawDetection]:
        from app.modules.ai.exceptions import ModelNotLoadedError

        if self._delegate is None:
            raise ModelNotLoadedError()
        return self._delegate.predict(frame, image_size, confidence, iou, allowed_class_ids, half)

    def warmup(self, image_size: int, iterations: int = 3) -> None:
        if self._delegate:
            self._delegate.warmup(image_size, iterations)

    def release(self) -> None:
        if self._delegate:
            self._delegate.release()
        self._delegate = None
