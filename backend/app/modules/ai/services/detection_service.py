"""
DetectionService — facade nghiệp vụ cho Detection Engine.

Điều phối ModelLoader + InferenceEngine + DetectionPipeline.
API layer chỉ gọi service. KHÔNG DB, KHÔNG alert, KHÔNG tracking.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

import numpy as np
from loguru import logger

from app.modules.ai.config import DetectionConfig
from app.modules.ai.detection.pipeline import DetectionPipeline
from app.modules.ai.inference.engine import InferenceEngine
from app.modules.ai.inference.model_loader import ModelLoader
from app.modules.ai.models import DetectionResult, ModelInfo


class DetectionStatistics:
    """
    Thống kê inference tích lũy — thread-safe.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_inferences = 0
        self.total_time_ms = 0.0
        self.total_objects = 0
        self.errors = 0

    def record(self, inference_ms: float, objects: int) -> None:
        """Ghi nhận một inference thành công."""
        with self._lock:
            self.total_inferences += 1
            self.total_time_ms += inference_ms
            self.total_objects += objects

    def record_error(self) -> None:
        """Ghi nhận một lỗi inference."""
        with self._lock:
            self.errors += 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize thống kê cho API."""
        with self._lock:
            avg_ms = (
                self.total_time_ms / self.total_inferences
                if self.total_inferences
                else 0.0
            )
            avg_fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0
            return {
                "total_inferences": self.total_inferences,
                "total_objects": self.total_objects,
                "errors": self.errors,
                "avg_inference_ms": round(avg_ms, 2),
                "avg_fps": round(avg_fps, 2),
            }


class DetectionService:
    """
    Service điều phối Detection Engine.

    Attributes:
        config: DetectionConfig.
        loader: ModelLoader.
        engine: InferenceEngine.
        pipeline: DetectionPipeline (multi-camera).
        statistics: Thống kê inference.
    """

    def __init__(self, config: DetectionConfig, perf_config=None) -> None:
        self._config = config
        backend_type = "pytorch"
        onnx_path = ""
        tensorrt_path = ""
        auto_export = False
        half = config.half_precision
        if perf_config is not None:
            backend_type = perf_config.backend.type
            onnx_path = perf_config.backend.onnx_path
            tensorrt_path = perf_config.backend.tensorrt_path
            auto_export = perf_config.backend.auto_export_onnx
            if perf_config.backend.precision == "fp16":
                half = True
        self.loader = ModelLoader(
            model_path=config.model.path,
            model_name=config.model.name,
            device=config.device,
            half_precision=half,
            image_size=config.image_size,
            class_labels=list(config.classes.keys()),
            backend_type=backend_type,
            onnx_path=onnx_path,
            tensorrt_path=tensorrt_path,
            auto_export_onnx=auto_export,
        )
        self.engine = InferenceEngine(self.loader, config)
        self.pipeline = DetectionPipeline(
            engine=self.engine,
            max_queue_size=config.queue.max_size,
            num_workers=config.queue.num_workers,
            poll_interval_ms=config.queue.poll_interval_ms,
            on_result=self._on_pipeline_result,
        )
        self.statistics = DetectionStatistics()
        self._detection_sink: Optional[Callable[[DetectionResult], None]] = None

    def set_detection_sink(
        self, sink: Optional[Callable[[DetectionResult], None]]
    ) -> None:
        """Đăng ký callback khi pipeline có kết quả (vd. đẩy lên WebSocket)."""
        self._detection_sink = sink

    # ----- Model lifecycle -----
    def load_model(self) -> ModelInfo:
        """Load + warmup model."""
        return self.loader.load(self._config.warmup_iterations)

    def reload_model(self) -> ModelInfo:
        """Reload model (đổi weight/thiết bị)."""
        return self.loader.reload(self._config.warmup_iterations)

    def get_model_info(self) -> ModelInfo:
        """Thông tin model hiện tại."""
        return self.loader.get_info()

    def release_model(self) -> None:
        """Giải phóng model."""
        self.loader.release()

    # ----- Inference -----
    def infer_frame(
        self,
        frame: np.ndarray,
        camera_id: int = 0,
        frame_id: int = 0,
    ) -> DetectionResult:
        """
        Inference đồng bộ một frame → DetectionResult.

        Args:
            frame: Ảnh BGR.
            camera_id: ID camera (metadata).
            frame_id: Số thứ tự frame.

        Returns:
            DetectionResult.
        """
        try:
            result = self.engine.infer(frame, camera_id, frame_id)
            self.statistics.record(result.inference_time_ms, result.count)
            return result
        except Exception:
            self.statistics.record_error()
            raise

    # ----- Multi-camera pipeline -----
    def start_pipeline(self) -> None:
        """Khởi động worker pipeline đa camera."""
        self.pipeline.start()

    def stop_pipeline(self) -> None:
        """Dừng pipeline."""
        self.pipeline.stop()

    def submit_frame(self, camera_id: int, frame: np.ndarray, frame_id: int) -> None:
        """Đẩy frame vào pipeline (non-blocking)."""
        self.pipeline.submit(camera_id, frame, frame_id)

    def get_latest_result(self, camera_id: int) -> Optional[DetectionResult]:
        """Kết quả mới nhất của camera trong pipeline."""
        return self.pipeline.get_latest_result(camera_id)

    def get_statistics(self) -> dict[str, Any]:
        """Thống kê inference + trạng thái pipeline."""
        stats = self.statistics.to_dict()
        stats["pipeline_processed"] = self.pipeline.processed_count
        stats["pipeline_running"] = self.pipeline.is_running
        stats["model_loaded"] = self.loader.is_loaded
        return stats

    def _on_pipeline_result(self, result: DetectionResult) -> None:
        """Callback pipeline — ghi thống kê + fan-out realtime nếu có sink."""
        self.statistics.record(result.inference_time_ms, result.count)
        if self._detection_sink is not None:
            try:
                self._detection_sink(result)
            except Exception as exc:
                logger.debug("Detection sink skipped: {}", exc)
