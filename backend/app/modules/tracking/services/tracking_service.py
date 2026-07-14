"""
TrackingService — facade multi-camera cho Tracking Engine.

Mỗi camera một TrackingEngine độc lập (không chia sẻ track id).
KHÔNG DB, KHÔNG alert, KHÔNG rule engine, KHÔNG telegram.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Tuple

from loguru import logger

from app.modules.ai.models import DetectionResult
from app.modules.tracking.config import TrackingConfig
from app.modules.tracking.models import Track, TrackingResult
from app.modules.tracking.repositories.tracking_repository import (
    InMemoryTrackingRepository,
)
from app.modules.tracking.tracking_engine.engine import TrackingEngine


class TrackingService:
    """Điều phối tracking cho nhiều camera."""

    def __init__(self, config: TrackingConfig) -> None:
        self._config = config
        self._engines: Dict[int, TrackingEngine] = {}
        self._repo = InMemoryTrackingRepository()
        self._lock = threading.RLock()

    def get_or_create_engine(self, camera_id: int) -> TrackingEngine:
        """Lấy engine của camera, tạo mới nếu chưa có (ROI theo cấu hình)."""
        with self._lock:
            engine = self._engines.get(camera_id)
            if engine is None:
                roi_configs = self._config.roi.for_camera(camera_id)
                engine = TrackingEngine(camera_id, self._config, roi_configs)
                self._engines[camera_id] = engine
                logger.info(
                    "TrackingEngine created | camera={} roi={}",
                    camera_id,
                    len(roi_configs),
                )
            return engine

    def process(self, detection: DetectionResult) -> TrackingResult:
        """
        Xử lý một DetectionResult → TrackingResult, lưu vào repository.

        Args:
            detection: DetectionResult từ Detection Engine.

        Returns:
            TrackingResult.
        """
        engine = self.get_or_create_engine(detection.camera_id)
        result = engine.update(detection)
        self._repo.save(result)
        return result

    # ----- Truy vấn -----
    def get_live(self) -> List[TrackingResult]:
        """Kết quả mới nhất của tất cả camera."""
        return self._repo.get_all_latest()

    def get_camera_result(self, camera_id: int) -> Optional[TrackingResult]:
        """Kết quả mới nhất của một camera."""
        return self._repo.get_latest(camera_id)

    def get_history(self, camera_id: int) -> List[TrackingResult]:
        """Lịch sử TrackingResult của một camera."""
        return self._repo.get_history(camera_id)

    def find_track(
        self, track_id: int, camera_id: Optional[int] = None
    ) -> List[Tuple[int, Track]]:
        """
        Tìm track theo id (id chỉ duy nhất trong phạm vi camera).

        Args:
            track_id: ID track.
            camera_id: Giới hạn theo camera (None = mọi camera).

        Returns:
            Danh sách (camera_id, Track) khớp.
        """
        with self._lock:
            engines = (
                [(camera_id, self._engines[camera_id])]
                if camera_id is not None and camera_id in self._engines
                else list(self._engines.items())
            )
        matches: List[Tuple[int, Track]] = []
        for cam_id, engine in engines:
            track = engine.get_track(track_id)
            if track is not None:
                matches.append((cam_id, track))
        return matches

    def statistics(self) -> dict:
        """Thống kê tổng hợp toàn bộ camera."""
        with self._lock:
            engines = list(self._engines.items())
        per_camera = {str(cam_id): eng.statistics() for cam_id, eng in engines}
        total_active = sum(s["active_tracks"] for s in per_camera.values())
        total_created = sum(s["total_created"] for s in per_camera.values())
        return {
            "cameras": len(per_camera),
            "total_active_tracks": total_active,
            "total_created": total_created,
            "per_camera": per_camera,
        }

    @property
    def config(self) -> TrackingConfig:
        """Cấu hình tracking."""
        return self._config
