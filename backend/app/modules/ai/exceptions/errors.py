"""
Exception hierarchy cho AI Detection Engine.

Tách riêng để module độc lập; map sang HTTP qua AEMSException base.
"""

from app.exceptions.base import AEMSException


class DetectionException(AEMSException):
    """Lớp cơ sở cho lỗi Detection Engine."""

    def __init__(self, message: str, code: str = "DETECTION_ERROR") -> None:
        super().__init__(message=message, code=code)


class ModelNotFoundError(DetectionException):
    """Không tìm thấy file weight model."""

    def __init__(self, path: str) -> None:
        super().__init__(message=f"Không tìm thấy model tại: {path}", code="MODEL_NOT_FOUND")


class ModelLoadError(DetectionException):
    """Lỗi khi load model (thiếu dependency, file hỏng...)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="MODEL_LOAD_ERROR")


class ModelNotLoadedError(DetectionException):
    """Gọi inference khi model chưa được load."""

    def __init__(self) -> None:
        super().__init__(
            message="Model chưa được load. Gọi reload hoặc bật auto_load.",
            code="MODEL_NOT_LOADED",
        )


class GPUOutOfMemoryError(DetectionException):
    """GPU hết bộ nhớ (CUDA OOM)."""

    def __init__(self, message: str = "GPU hết bộ nhớ (CUDA OOM).") -> None:
        super().__init__(message=message, code="GPU_OUT_OF_MEMORY")


class CUDAError(DetectionException):
    """Lỗi CUDA/driver GPU."""

    def __init__(self, message: str = "Lỗi CUDA/GPU.") -> None:
        super().__init__(message=message, code="CUDA_ERROR")


class InvalidFrameError(DetectionException):
    """Frame đầu vào không hợp lệ (None, sai shape, sai dtype)."""

    def __init__(self, message: str = "Frame không hợp lệ.") -> None:
        super().__init__(message=message, code="INVALID_FRAME")


class InferenceTimeoutError(DetectionException):
    """Inference vượt quá thời gian cho phép."""

    def __init__(self, timeout_s: float) -> None:
        super().__init__(
            message=f"Inference timeout sau {timeout_s}s.", code="INFERENCE_TIMEOUT"
        )


class InferenceError(DetectionException):
    """Lỗi chung trong quá trình inference."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INFERENCE_ERROR")
