"""
YOLOPoseEstimator — pose estimation bằng Ultralytics YOLO11-pose.

Lazy import ultralytics/torch để module import an toàn khi chưa cài.
"""

from __future__ import annotations

from typing import List

import numpy as np
from loguru import logger

from app.modules.behavior.config import PoseConfig
from app.modules.behavior.exceptions import (
    PoseError,
    PoseModelLoadError,
    PoseModelNotLoadedError,
)
from app.modules.behavior.models import Keypoints, PoseResult
from app.modules.behavior.pose.estimator import PoseEstimator


class YOLOPoseEstimator(PoseEstimator):
    """Pose estimator dùng YOLO11-pose (17 keypoint COCO)."""

    def __init__(self, config: PoseConfig) -> None:
        self._config = config
        self._model = None
        self._device = config.device

    @property
    def name(self) -> str:
        """Tên model."""
        return f"yolo-pose:{self._config.model_path}"

    @property
    def is_loaded(self) -> bool:
        """Đã load chưa."""
        return self._model is not None

    def load(self) -> None:
        """Nạp YOLO pose + warmup."""
        from app.modules.ai.utils.device import resolve_device

        self._device = resolve_device(self._config.device)
        try:
            from ultralytics import YOLO
        except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
            raise PoseModelLoadError(f"Chưa cài ultralytics/torch: {exc}") from exc
        try:
            model = YOLO(self._config.model_path)
            model.to(self._device)
            self._model = model
        except Exception as exc:  # pragma: no cover
            raise PoseModelLoadError(f"Lỗi nạp pose model: {exc}") from exc

        logger.info("Pose model loaded | {} device={}", self.name, self._device)
        self._warmup()

    def _warmup(self) -> None:
        """Warmup pose model."""
        if self._model is None:
            return
        dummy = np.zeros(
            (self._config.image_size, self._config.image_size, 3), dtype=np.uint8
        )
        for _ in range(max(0, self._config.warmup_iterations)):
            self._model.predict(
                dummy,
                imgsz=self._config.image_size,
                device=self._device,
                half=self._config.half_precision,
                verbose=False,
            )

    def estimate(self, frame: np.ndarray) -> List[PoseResult]:
        """Chạy pose và parse thành PoseResult."""
        if self._model is None:
            raise PoseModelNotLoadedError()
        try:
            results = self._model.predict(
                frame,
                imgsz=self._config.image_size,
                conf=self._config.confidence,
                device=self._device,
                half=self._config.half_precision,
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover - phụ thuộc GPU
            raise PoseError(str(exc)) from exc
        return self._parse(results)

    def _parse(self, results) -> List[PoseResult]:
        """Chuyển ultralytics keypoints → PoseResult."""
        poses: List[PoseResult] = []
        if not results:
            return poses
        r0 = results[0]
        boxes = getattr(r0, "boxes", None)
        kpts = getattr(r0, "keypoints", None)
        if boxes is None or kpts is None:
            return poses

        xy = kpts.xy.cpu().numpy() if hasattr(kpts.xy, "cpu") else np.asarray(kpts.xy)
        conf = (
            kpts.conf.cpu().numpy()
            if getattr(kpts, "conf", None) is not None and hasattr(kpts.conf, "cpu")
            else None
        )
        for i, box in enumerate(boxes):
            xyxy = box.xyxy[0].tolist()
            score = float(box.conf[0].item()) if box.conf is not None else 1.0
            person_xy = xy[i]
            person_conf = conf[i] if conf is not None else np.ones(len(person_xy))
            points = [
                (float(person_xy[j][0]), float(person_xy[j][1]), float(person_conf[j]))
                for j in range(len(person_xy))
            ]
            poses.append(
                PoseResult(
                    bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                    score=score,
                    keypoints=Keypoints(points, self._config.keypoint_confidence),
                )
            )
        return poses

    def release(self) -> None:
        """Giải phóng model + VRAM."""
        self._model = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # pragma: no cover
            pass
