"""
Unit tests — TrackManager: vòng đời NEW/TRACKING/LOST/RECOVERED/REMOVED + ROI.
"""

from datetime import timedelta

from app.modules.ai.models import utc_now
from app.modules.tracking.config import LifecycleConfig, ROIRegionConfig
from app.modules.tracking.models import TrackedObject, TrackState
from app.modules.tracking.roi.roi_manager import ROIManager
from app.modules.tracking.timeline.motion import MotionAnalyzer
from app.modules.tracking.track_manager.manager import TrackManager


def _make_manager(max_lost: int = 3) -> TrackManager:
    roi_cfg = ROIRegionConfig(
        id="desk_01",
        name="Desk 01",
        polygon=[[0, 0], [320, 0], [320, 240], [0, 240]],
    )
    return TrackManager(
        camera_id=1,
        lifecycle=LifecycleConfig(max_lost_frames=max_lost, max_tracks=300),
        roi_manager=ROIManager.from_config([roi_cfg]),
        motion_analyzer=MotionAnalyzer(2.0, 1000.0),
        history_size=30,
    )


def _obj(track_id: int, x: float = 50, y: float = 50) -> TrackedObject:
    return TrackedObject(track_id=track_id, xyxy=(x, y, x + 40, y + 100), score=0.9)


class TestTrackLifecycle:
    """Test chuyển trạng thái track."""

    def test_create_new(self) -> None:
        """Frame đầu → NEW."""
        tm = _make_manager()
        now = utc_now()
        active = tm.update([_obj(1)], frame_id=0, timestamp=now)
        assert len(active) == 1
        assert active[0].status == TrackState.NEW

    def test_new_to_tracking(self) -> None:
        """Frame kế → TRACKING."""
        tm = _make_manager()
        now = utc_now()
        tm.update([_obj(1)], 0, now)
        active = tm.update([_obj(1, x=52)], 1, now + timedelta(seconds=1 / 30))
        assert active[0].status == TrackState.TRACKING

    def test_lost_then_recovered(self) -> None:
        """Mất 1 frame → LOST; quay lại → RECOVERED."""
        tm = _make_manager()
        now = utc_now()
        tm.update([_obj(1)], 0, now)
        tm.update([], 1, now + timedelta(seconds=1 / 30))  # missing → LOST
        track = tm.get_track(1)
        assert track.status == TrackState.LOST
        assert track.timeline.lost_count == 1

        active = tm.update([_obj(1, x=54)], 2, now + timedelta(seconds=2 / 30))
        assert active[0].status == TrackState.RECOVERED
        assert active[0].timeline.recover_count == 1

    def test_removed_after_timeout(self) -> None:
        """Mất quá max_lost_frames → REMOVED + vào history."""
        tm = _make_manager(max_lost=2)
        now = utc_now()
        tm.update([_obj(1)], 0, now)
        # Mất liên tục cho tới khi vượt ngưỡng
        for f in range(1, 6):
            tm.update([], f, now + timedelta(seconds=f / 30))
        assert tm.get_track(1) is not None  # còn trong history
        assert any(t.track_id == 1 for t in tm.get_history())
        # Không còn active
        assert all(t.track_id != 1 for t in tm.get_active_tracks())


class TestTrackROI:
    """Test gán ROI cho track."""

    def test_track_inside_roi(self) -> None:
        """Track trong ROI → current_roi_id set + timeline visit."""
        tm = _make_manager()
        now = utc_now()
        active = tm.update([_obj(1, x=50, y=50)], 0, now)
        assert active[0].current_roi_id == "desk_01"
        assert len(active[0].timeline.roi_history) == 1

    def test_track_outside_roi(self) -> None:
        """Track ngoài ROI → current_roi_id None."""
        tm = _make_manager()
        now = utc_now()
        active = tm.update([_obj(1, x=500, y=500)], 0, now)
        assert active[0].current_roi_id is None


class TestTrackStatistics:
    """Test thống kê."""

    def test_statistics_counts(self) -> None:
        tm = _make_manager()
        now = utc_now()
        tm.update([_obj(1), _obj(2, x=400, y=300)], 0, now)
        stats = tm.statistics()
        assert stats["total_created"] == 2
        assert stats["active_tracks"] == 2
