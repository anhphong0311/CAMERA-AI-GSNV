"""Factory tạo pose estimator theo config — đổi model không đổi business logic."""

from __future__ import annotations

from app.modules.behavior.config import PoseConfig
from app.modules.behavior.pose.estimator import PoseEstimator


def create_pose_estimator(config: PoseConfig) -> PoseEstimator:
    """
    Tạo pose estimator theo config.pose.type.

    Hiện hỗ trợ: yolo. Thêm mediapipe = thêm nhánh ở đây, KHÔNG đổi
    feature extractors / engine / service / API.

    Args:
        config: PoseConfig.

    Returns:
        PoseEstimator.

    Raises:
        ValueError: Loại pose model chưa hỗ trợ.
    """
    pose_type = config.type.lower()
    if pose_type == "yolo":
        from app.modules.behavior.pose.yolo_pose import YOLOPoseEstimator

        return YOLOPoseEstimator(config)
    if pose_type == "mediapipe":
        raise ValueError(
            "MediaPipe pose chưa cài đặt trong Sprint 5 (interface đã sẵn sàng mở rộng)."
        )
    raise ValueError(f"Loại pose model chưa hỗ trợ: {config.type}")
