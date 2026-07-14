"""Exceptions package — AI Detection Engine."""

from app.modules.ai.exceptions.errors import (
    CUDAError,
    DetectionException,
    GPUOutOfMemoryError,
    InferenceError,
    InferenceTimeoutError,
    InvalidFrameError,
    ModelLoadError,
    ModelNotFoundError,
    ModelNotLoadedError,
)

__all__ = [
    "CUDAError",
    "DetectionException",
    "GPUOutOfMemoryError",
    "InferenceError",
    "InferenceTimeoutError",
    "InvalidFrameError",
    "ModelLoadError",
    "ModelNotFoundError",
    "ModelNotLoadedError",
]
