"""
Unit tests — Timeline (ROI enter/leave/stay) và Motion (direction/speed).
"""

from datetime import timedelta

from app.modules.ai.models import utc_now
from app.modules.tracking.models import ROI, Timeline
from app.modules.tracking.timeline.motion import MotionAnalyzer, compute_direction
from app.modules.tracking.timeline.timeline_manager import TimelineManager


class TestMotionDirection:
    """Test suy hướng chuyển động."""

    def test_right(self) -> None:
        assert compute_direction(5, 0, 2.0) == "RIGHT"

    def test_down(self) -> None:
        # Trục y ảnh hướng xuống → vy>0 là DOWN
        assert compute_direction(0, 5, 2.0) == "DOWN"

    def test_up(self) -> None:
        assert compute_direction(0, -5, 2.0) == "UP"

    def test_stationary(self) -> None:
        assert compute_direction(0.5, 0.5, 2.0) == "STATIONARY"


class TestMotionAnalyzer:
    """Test tính vận tốc/tốc độ."""

    def test_velocity_and_speed(self) -> None:
        analyzer = MotionAnalyzer(stationary_speed=2.0, frame_diagonal=1000.0)
        state = analyzer.analyze((0, 0), (10, 0), dt_frames=1.0)
        assert state.velocity == (10.0, 0.0)
        assert state.speed_px == 10.0
        assert state.direction == "RIGHT"
        assert state.speed_norm == 0.01

    def test_no_prev_center(self) -> None:
        """Track mới (chưa có prev) → đứng yên."""
        analyzer = MotionAnalyzer(2.0, 1000.0)
        state = analyzer.analyze(None, (10, 10))
        assert state.speed_px == 0.0
        assert state.direction == "STATIONARY"


class TestTimelineManager:
    """Test cập nhật timeline + ROI transition."""

    def _timeline(self):
        now = utc_now()
        return Timeline(
            first_seen=now, last_seen=now, first_frame=0, last_frame=0, history_size=10
        ), now

    def test_enter_roi_records_visit(self) -> None:
        """Vào ROI → tạo ROIVisit."""
        timeline, now = self._timeline()
        roi = ROI("desk", "Desk", [(0, 0), (100, 0), (100, 100), (0, 100)])
        events = TimelineManager.update(timeline, 1, (50, 50), 1, now, roi)
        assert any(e.kind == "enter" for e in events)
        assert len(timeline.roi_history) == 1
        assert timeline.roi_history[0].roi_id == "desk"

    def test_stay_time_accumulates(self) -> None:
        """Ở trong ROI → stay_seconds tăng."""
        timeline, now = self._timeline()
        roi = ROI("desk", "Desk", [(0, 0), (100, 0), (100, 100), (0, 100)])
        TimelineManager.update(timeline, 1, (50, 50), 1, now, roi)
        later = now + timedelta(seconds=5)
        TimelineManager.update(timeline, 1, (55, 55), 2, later, roi)
        assert timeline.roi_history[0].stay_seconds >= 5.0

    def test_leave_roi_closes_visit(self) -> None:
        """Rời ROI → leave_time được set."""
        timeline, now = self._timeline()
        roi = ROI("desk", "Desk", [(0, 0), (100, 0), (100, 100), (0, 100)])
        TimelineManager.update(timeline, 1, (50, 50), 1, now, roi)
        later = now + timedelta(seconds=2)
        events = TimelineManager.update(timeline, 1, (500, 500), 2, later, None)
        assert any(e.kind == "leave" for e in events)
        assert timeline.roi_history[0].leave_time is not None

    def test_path_bounded(self) -> None:
        """movement_history giới hạn theo history_size."""
        timeline, now = self._timeline()
        for f in range(20):
            TimelineManager.update(timeline, 1, (f, f), f, now, None)
        assert len(timeline.movement_history) <= 10
