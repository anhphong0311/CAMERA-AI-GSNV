"""
Exception hierarchy cho Behavior Feature Engine.
"""

from app.exceptions.base import AEMSException


class BehaviorException(AEMSException):
    """Lớp cơ sở cho lỗi Behavior Engine."""

    def __init__(self, message: str, code: str = "BEHAVIOR_ERROR") -> None:
        super().__init__(message=message, code=code)


class PoseError(BehaviorException):
    """Lỗi khi chạy pose estimation."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="POSE_ERROR")


class PoseModelLoadError(BehaviorException):
    """Lỗi nạp pose model (thiếu ultralytics/torch/weight)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="POSE_MODEL_LOAD_ERROR")


class PoseModelNotLoadedError(BehaviorException):
    """Gọi pose khi model chưa load."""

    def __init__(self) -> None:
        super().__init__(
            message="Pose model chưa được load.", code="POSE_MODEL_NOT_LOADED"
        )


class InvalidSkeletonError(BehaviorException):
    """Skeleton không hợp lệ (thiếu quá nhiều keypoint)."""

    def __init__(self, message: str = "Skeleton không hợp lệ.") -> None:
        super().__init__(message=message, code="INVALID_SKELETON")


class MissingJointError(BehaviorException):
    """Thiếu joint bắt buộc để tính đặc trưng."""

    def __init__(self, joint: str) -> None:
        super().__init__(message=f"Thiếu joint: {joint}", code="MISSING_JOINT")


class BufferOverflowError(BehaviorException):
    """Tràn temporal buffer."""

    def __init__(self, message: str = "Tràn temporal buffer.") -> None:
        super().__init__(message=message, code="BUFFER_OVERFLOW")
