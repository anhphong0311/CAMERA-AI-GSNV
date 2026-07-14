"""
Integration test — Detection Engine (Sprint 3) → Tracking Engine (Sprint 4).

Mô phỏng DetectionResult (như đầu ra Detection Engine), chạy tracking,
kiểm tra Track ID ổn định, ROI, duration, motion path, đa camera độc lập,
và overlay visualization.

KHÔNG lưu Database. KHÔNG Telegram. KHÔNG chạy YOLO.
"""

from datetime import timedelta

import numpy as np

from app.modules.ai.models import utc_now
from app.modules.tracking.config import ROIRegionConfig
from app.modules.tracking.models import TrackState
from app.modules.tracking.services.tracking_service import TrackingService
from app.modules.tracking.tracking_engine.engine import TrackingEngine
from app.modules.tracking.utils.visualizer import draw_tracks

from tests.modules.tracking.conftest import make_detection_result


class TestDetectionToTracking:
    """Detection → Tracking pipeline."""

    def test_track_20_people_stable_ids(self, tracking_config) -> None:
        """>= 20 người cùng lúc, ID ổn định, không đổi liên tục."""
        engine = TrackingEngine(1, tracking_config, [])
        base = utc_now()
        for f in range(15):
            boxes = [
                (pid * 55 + f * 3, (pid * 30) % 600, pid * 55 + f * 3 + 40, (pid * 30) % 600 + 100)
                for pid in range(20)
            ]
            dr = make_detection_result(1, f, boxes, base_time=base)
            result = engine.update(dr)
        assert result.count == 20
        stats = engine.statistics()
        # ID ổn định: số track tạo ra = số người (không ID switch)
        assert stats["total_created"] == 20

    def test_duration_and_motion(self, tracking_config) -> None:
        """Tính duration (thời gian xuất hiện) + hướng di chuyển."""
        engine = TrackingEngine(1, tracking_config, [])
        base = utc_now()
        result = None
        for f in range(10):
            x = 100 + f * 5
            dr = make_detection_result(1, f, [(x, 100, x + 40, 200)], base_time=base)
            result = engine.update(dr)
        track = result.tracks[0]
        assert track.duration > 0
        assert track.direction == "RIGHT"  # di chuyển sang phải
        assert len(track.timeline.path()) >= 2

    def test_roi_stay_time(self, tracking_config, sample_roi_config) -> None:
        """Theo dõi ROI + tính thời gian trong ROI."""
        engine = TrackingEngine(1, tracking_config, [sample_roi_config])
        base = utc_now()
        result = None
        for f in range(10):
            # Đứng yên trong ROI desk_01 (0..320, 0..240)
            dr = make_detection_result(1, f, [(100, 100, 140, 200)], base_time=base)
            result = engine.update(dr)
        track = result.tracks[0]
        assert track.current_roi_id == "desk_01"
        assert track.timeline.roi_history[0].stay_seconds > 0

    def test_ignores_non_person(self, tracking_config) -> None:
        """Detection không phải person bị bỏ qua (Sprint 4 chỉ theo dõi người)."""
        engine = TrackingEngine(1, tracking_config, [])
        base = utc_now()
        dr = make_detection_result(
            1, 0, [(10, 10, 50, 110)], base_time=base, class_name="phone"
        )
        result = engine.update(dr)
        assert result.count == 0

    def test_overlay_visualization(self, tracking_config, sample_roi_config) -> None:
        """Overlay track/ROI/path tạo ảnh, không sửa gốc."""
        engine = TrackingEngine(1, tracking_config, [sample_roi_config])
        base = utc_now()
        result = None
        for f in range(5):
            x = 50 + f * 5
            dr = make_detection_result(1, f, [(x, 50, x + 40, 150)], base_time=base)
            result = engine.update(dr)
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        canvas = draw_tracks(frame, result, engine.roi_manager, camera_name="cam-1")
        assert canvas.shape == frame.shape
        assert canvas.sum() > 0
        assert frame.sum() == 0


class TestMultiCameraIndependence:
    """Đa camera — track ID độc lập, không chia sẻ."""

    def test_independent_track_ids(self, tracking_config) -> None:
        """2 camera → ID đánh số độc lập, bắt đầu từ 1."""
        service = TrackingService(tracking_config)
        base = utc_now()
        dr_a = make_detection_result(1, 0, [(10, 10, 50, 110)], base_time=base)
        dr_b = make_detection_result(2, 0, [(500, 500, 540, 600)], base_time=base)
        res_a = service.process(dr_a)
        res_b = service.process(dr_b)
        # Cả 2 camera đều có track id = 1 (độc lập, không chia sẻ)
        assert res_a.tracks[0].track_id == 1
        assert res_b.tracks[0].track_id == 1
        assert res_a.camera_id == 1
        assert res_b.camera_id == 2

    def test_live_and_history(self, tracking_config) -> None:
        """Live trả mọi camera; history lưu theo camera."""
        service = TrackingService(tracking_config)
        base = utc_now()
        for f in range(3):
            service.process(make_detection_result(1, f, [(10, 10, 50, 110)], base_time=base))
            service.process(make_detection_result(2, f, [(20, 20, 60, 120)], base_time=base))
        live = service.get_live()
        assert len(live) == 2
        assert len(service.get_history(1)) == 3

    def test_find_track_scoped_to_camera(self, tracking_config) -> None:
        """find_track giới hạn theo camera."""
        service = TrackingService(tracking_config)
        base = utc_now()
        service.process(make_detection_result(1, 0, [(10, 10, 50, 110)], base_time=base))
        service.process(make_detection_result(2, 0, [(10, 10, 50, 110)], base_time=base))
        matches_all = service.find_track(1)
        matches_cam1 = service.find_track(1, camera_id=1)
        assert len(matches_all) == 2  # cả 2 camera có track id 1
        assert len(matches_cam1) == 1
        assert matches_cam1[0][0] == 1
