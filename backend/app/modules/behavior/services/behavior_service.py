"""
BehaviorService — facade đa camera cho Behavior Feature Engine.

Giữ 1 PoseEstimator dùng chung (model nặng) + BehaviorFeatureEngine mỗi camera
(HistoryManager độc lập) + BehaviorRepository (in-memory).
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Sequence

import numpy as np
from loguru import logger

from app.modules.behavior.config import BehaviorConfig, load_behavior_config
from app.modules.behavior.feature_engine import BehaviorFeatureEngine
from app.modules.behavior.models import BehaviorFeatureDTO, BehaviorResult, PoseResult
from app.modules.behavior.pose import PoseEstimator, create_pose_estimator
from app.modules.behavior.repositories import BehaviorRepository


class BehaviorService:
    """Điều phối pose + trích đặc trưng cho nhiều camera."""

    def __init__(
        self,
        config: Optional[BehaviorConfig] = None,
        pose_estimator: Optional[PoseEstimator] = None,
    ) -> None:
        self._config = config or load_behavior_config()
        self._pose = pose_estimator or create_pose_estimator(self._config.pose)
        self._engines: Dict[int, BehaviorFeatureEngine] = {}
        self._repo = BehaviorRepository()
        self._lock = threading.RLock()

    @property
    def config(self) -> BehaviorConfig:
        """Cấu hình hiện tại."""
        return self._config

    @property
    def pose_loaded(self) -> bool:
        """Pose model đã load chưa."""
        return self._pose.is_loaded

    def load_pose(self) -> None:
        """Nạp pose model (bỏ qua nếu lỗi môi trường — degrade motion-only)."""
        try:
            self._pose.load()
        except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
            logger.warning("Không nạp được pose model ({}). Chạy motion-only.", exc)

    def _engine(self, camera_id: int) -> BehaviorFeatureEngine:
        """Lấy/tạo engine cho camera."""
        eng = self._engines.get(camera_id)
        if eng is None:
            eng = BehaviorFeatureEngine(camera_id, self._config)
            self._engines[camera_id] = eng
        return eng

    def process(
        self,
        frame: Optional[np.ndarray],
        tracking_result,
        detections: Optional[Sequence] = None,
        poses: Optional[List[PoseResult]] = None,
    ) -> BehaviorResult:
        """
        Trích đặc trưng hành vi cho một frame.

        Args:
            frame: Ảnh BGR (dùng chạy pose). Có thể None nếu truyền poses sẵn.
            tracking_result: TrackingResult (Sprint 4).
            detections: Detection objects (ngữ cảnh); có thể None.
            poses: PoseResult tính sẵn (test/tùy chọn); None → tự chạy pose.

        Returns:
            BehaviorResult.
        """
        if poses is None:
            if self._pose.is_loaded and frame is not None:
                logger.debug("Pose started cam={}", tracking_result.camera_id)
                poses = self._pose.estimate(frame)
                logger.debug(
                    "Pose finished cam={} persons={}",
                    tracking_result.camera_id,
                    len(poses),
                )
            else:
                poses = []

        with self._lock:
            engine = self._engine(tracking_result.camera_id)
        result = engine.process(tracking_result, poses, detections)
        self._repo.save(result)
        logger.debug(
            "Feature extracted cam={} frame={} count={}",
            result.camera_id,
            result.frame_id,
            result.count,
        )
        return result

    def get_live(self) -> List[BehaviorResult]:
        """Kết quả mới nhất tất cả camera."""
        return self._repo.get_live()

    def get_camera(self, camera_id: int) -> Optional[BehaviorResult]:
        """Kết quả mới nhất của camera."""
        return self._repo.get_camera(camera_id)

    def get_track(self, track_id: int) -> Optional[BehaviorFeatureDTO]:
        """Đặc trưng mới nhất của track."""
        entry = self._repo.get_track(track_id)
        return entry[1] if entry else None

    def statistics(self) -> dict:
        """Thống kê."""
        stats = self._repo.statistics()
        stats["pose_model"] = self._pose.name
        stats["pose_loaded"] = self._pose.is_loaded
        stats["cameras"] = len(self._engines)
        return stats

    def shutdown(self) -> None:
        """Giải phóng pose model + xóa state."""
        try:
            self._pose.release()
        except Exception:  # pragma: no cover
            pass
        self._engines.clear()
        self._repo.clear()
        logger.info("BehaviorService shutdown.")
