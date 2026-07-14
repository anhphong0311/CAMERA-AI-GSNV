"""
InferenceEngine — chạy inference trên một frame và trả DetectionResult.

Luồng: validate → backend.predict → postprocess → DetectionResult DTO.
Thread-safe (lock quanh model call — GPU chạy tuần tự).
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import numpy as np

from app.modules.ai.config import DetectionConfig
from app.modules.ai.exceptions import ModelNotLoadedError
from app.modules.ai.inference.model_loader import ModelLoader
from app.modules.ai.models import DetectionResult, utc_now
from app.modules.ai.postprocess.postprocessor import ImagePostprocessor
from app.modules.ai.preprocess.preprocessor import ImagePreprocessor


class InferenceEngine:
    """
    Bộ máy inference — orchestrate preprocess + backend + postprocess.

    Không biết DB/tracking/telegram. Chỉ frame → DetectionResult.
    """

    def __init__(
        self,
        loader: ModelLoader,
        config: DetectionConfig,
        preprocessor: Optional[ImagePreprocessor] = None,
        postprocessor: Optional[ImagePostprocessor] = None,
    ) -> None:
        self._loader = loader
        self._config = config
        self._pre = preprocessor or ImagePreprocessor(config.image_size)
        self._post = postprocessor or ImagePostprocessor(
            class_map=config.build_class_map(),
            max_detections=config.max_detections,
        )
        self._infer_lock = threading.Lock()

    @property
    def loader(self) -> ModelLoader:
        """ModelLoader gắn với engine."""
        return self._loader

    def infer(
        self,
        frame: np.ndarray,
        camera_id: int = 0,
        frame_id: int = 0,
    ) -> DetectionResult:
        """
        Chạy detection trên một frame.

        Args:
            frame: Ảnh BGR gốc (numpy).
            camera_id: ID camera nguồn (metadata, không tra DB).
            frame_id: Số thứ tự frame.

        Returns:
            DetectionResult: DTO chuẩn.

        Raises:
            ModelNotLoadedError: Model chưa load.
            InvalidFrameError: Frame không hợp lệ.
        """
        # Validate frame trước (bắt lỗi sớm, không cần lock)
        self._pre.validate(frame)

        backend = self._loader.backend
        if backend is None:
            raise ModelNotLoadedError()

        height, width = frame.shape[:2]
        start = time.perf_counter()

        # Lock quanh model call — GPU/model không reentrant
        with self._infer_lock:
            raws = backend.predict(
                frame=frame,
                image_size=self._config.image_size,
                confidence=self._config.min_confidence(),
                iou=self._config.nms_iou,
                allowed_class_ids=self._config.allowed_class_ids(),
                half=self._config.half_precision,
            )

        # Postprocess: Ultralytics đã NMS + map tọa độ → apply_nms=False.
        # Vẫn cần áp ngưỡng confidence riêng theo class + dựng DTO.
        detections = self._post.process(raws, apply_nms=False)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return DetectionResult(
            camera_id=camera_id,
            frame_id=frame_id,
            timestamp=utc_now(),
            objects=detections,
            inference_time_ms=elapsed_ms,
            model_name=self._loader.model_name,
            width=width,
            height=height,
        )
