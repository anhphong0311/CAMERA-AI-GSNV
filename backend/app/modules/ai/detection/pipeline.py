"""
DetectionPipeline — điều phối inference đa camera.

Mỗi camera có AIFrameQueue riêng (drop-oldest). Một pool worker thread
lấy frame theo vòng (round-robin fair) và chạy InferenceEngine.
=> Một camera nghẽn không block camera khác.

Kết quả mới nhất mỗi camera được giữ lại + gọi callback tùy chọn.
Pipeline KHÔNG lưu DB, KHÔNG gửi alert — chỉ trả DetectionResult.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Dict, List, Optional

import numpy as np
from loguru import logger

from app.modules.ai.detection.frame_queue import AIFrameQueue
from app.modules.ai.inference.engine import InferenceEngine
from app.modules.ai.models import DetectionResult

ResultCallback = Callable[[DetectionResult], None]


class DetectionPipeline:
    """
    Pipeline inference đa camera với queue riêng từng camera.

    Attributes:
        max_queue_size: Kích thước queue mỗi camera.
        num_workers: Số worker thread xử lý inference.
    """

    def __init__(
        self,
        engine: InferenceEngine,
        max_queue_size: int = 5,
        num_workers: int = 2,
        poll_interval_ms: int = 5,
        on_result: Optional[ResultCallback] = None,
    ) -> None:
        self._engine = engine
        self._max_queue_size = max_queue_size
        self._num_workers = num_workers
        self._poll_interval = poll_interval_ms / 1000.0
        self._on_result = on_result

        self._queues: Dict[int, AIFrameQueue] = {}
        self._latest_results: Dict[int, DetectionResult] = {}
        self._lock = threading.RLock()
        self._threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._processed_count = 0
        self._rr_index = 0

    # ----- Quản lý camera -----
    def register_camera(self, camera_id: int) -> None:
        """Tạo queue riêng cho camera nếu chưa có."""
        with self._lock:
            if camera_id not in self._queues:
                self._queues[camera_id] = AIFrameQueue(
                    camera_id, self._max_queue_size
                )
                logger.info("Detection pipeline registered camera_id={}", camera_id)

    def unregister_camera(self, camera_id: int) -> None:
        """Gỡ camera khỏi pipeline."""
        with self._lock:
            self._queues.pop(camera_id, None)
            self._latest_results.pop(camera_id, None)

    def submit(self, camera_id: int, frame: np.ndarray, frame_id: int) -> None:
        """
        Đẩy frame của camera vào queue (non-blocking).

        Args:
            camera_id: ID camera.
            frame: Ảnh BGR.
            frame_id: Số thứ tự frame.
        """
        with self._lock:
            queue = self._queues.get(camera_id)
            if queue is None:
                self.register_camera(camera_id)
                queue = self._queues[camera_id]
        queue.put(frame_id, frame)

    def get_latest_result(self, camera_id: int) -> Optional[DetectionResult]:
        """Kết quả detection mới nhất của camera (None nếu chưa có)."""
        with self._lock:
            return self._latest_results.get(camera_id)

    @property
    def processed_count(self) -> int:
        """Tổng số frame đã inference."""
        with self._lock:
            return self._processed_count

    @property
    def is_running(self) -> bool:
        """Pipeline có worker đang chạy không."""
        return any(t.is_alive() for t in self._threads)

    # ----- Vòng đời worker -----
    def start(self) -> None:
        """Khởi động pool worker thread."""
        with self._lock:
            if self.is_running:
                return
            self._stop_event.clear()
            self._threads = [
                threading.Thread(
                    target=self._worker_loop,
                    name=f"ai-detection-worker-{i}",
                    daemon=True,
                )
                for i in range(self._num_workers)
            ]
            for t in self._threads:
                t.start()
            logger.info("Detection pipeline started | workers={}", self._num_workers)

    def stop(self, timeout: float = 5.0) -> None:
        """Dừng toàn bộ worker."""
        self._stop_event.set()
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=timeout)
        self._threads = []
        logger.info("Detection pipeline stopped")

    def _next_frame(self) -> Optional[object]:
        """
        Lấy frame kế tiếp theo round-robin công bằng giữa các camera.

        Returns:
            QueuedFrame hoặc None nếu mọi queue rỗng.
        """
        with self._lock:
            if not self._queues:
                return None
            camera_ids = sorted(self._queues.keys())
            n = len(camera_ids)
            for _ in range(n):
                cam_id = camera_ids[self._rr_index % n]
                self._rr_index = (self._rr_index + 1) % n
                item = self._queues[cam_id].get()
                if item is not None:
                    return item
        return None

    def _worker_loop(self) -> None:
        """Vòng lặp worker — lấy frame, inference, lưu kết quả. Không crash."""
        while not self._stop_event.is_set():
            item = self._next_frame()
            if item is None:
                time.sleep(self._poll_interval)
                continue
            try:
                result = self._engine.infer(
                    frame=item.frame,
                    camera_id=item.camera_id,
                    frame_id=item.frame_id,
                )
                with self._lock:
                    self._latest_results[item.camera_id] = result
                    self._processed_count += 1
                if self._on_result:
                    try:
                        self._on_result(result)
                    except Exception as cb_exc:  # callback lỗi không làm chết worker
                        logger.warning("Detection result callback error | {}", cb_exc)
            except Exception as exc:
                logger.error(
                    "Inference error | camera_id={} frame_id={} err={}",
                    item.camera_id,
                    item.frame_id,
                    exc,
                )
