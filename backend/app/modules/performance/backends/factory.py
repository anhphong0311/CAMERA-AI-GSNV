"""
Backend factory — chọn PyTorch / ONNX / TensorRT theo config.

Export YOLO → ONNX (Ultralytics) khi `auto_export_onnx=true`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from loguru import logger

from app.modules.ai.inference.backend import InferenceBackend, UltralyticsBackend


BackendType = Literal["pytorch", "onnx", "tensorrt"]


def export_yolo_to_onnx(pt_path: str, onnx_path: str, image_size: int = 640) -> str:
    """Export weight .pt sang ONNX qua Ultralytics."""
    from ultralytics import YOLO

    out = Path(onnx_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    model = YOLO(pt_path)
    model.export(format="onnx", imgsz=image_size, simplify=True)
    exported = Path(pt_path).with_suffix(".onnx")
    if exported.exists() and exported != out:
        exported.replace(out)
    logger.info("Exported ONNX | {} → {}", pt_path, out)
    return str(out)


def create_backend(
    backend_type: BackendType,
    *,
    model_path: str,
    onnx_path: str,
    tensorrt_path: str,
    device: str,
    half: bool,
    auto_export_onnx: bool = False,
    image_size: int = 640,
) -> InferenceBackend:
    """
    Factory tạo InferenceBackend theo loại.

    Không thay đổi InferenceEngine — chỉ inject backend khác.
    """
    if backend_type == "pytorch":
        backend = UltralyticsBackend(model_path, device, half)
        backend.load()
        return backend

    if backend_type == "onnx":
        from app.modules.performance.backends.onnx_backend import ONNXBackend

        path = Path(onnx_path)
        if not path.exists() and auto_export_onnx and Path(model_path).exists():
            export_yolo_to_onnx(model_path, onnx_path, image_size)
        backend = ONNXBackend(str(path), device, half)
        backend.load()
        return backend

    if backend_type == "tensorrt":
        from app.modules.performance.backends.tensorrt_backend import TensorRTBackend

        onnx = Path(onnx_path)
        if not onnx.exists() and auto_export_onnx and Path(model_path).exists():
            export_yolo_to_onnx(model_path, onnx_path, image_size)
        backend = TensorRTBackend(tensorrt_path, onnx_path, device, half)
        backend.load()
        return backend

    raise ValueError(f"Backend không hỗ trợ: {backend_type}")
