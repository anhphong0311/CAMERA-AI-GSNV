"""
Unit tests — DTO TrackingResult / Track serialize.
"""

from app.modules.ai.models import utc_now
from app.modules.tracking.models import Timeline, Track, TrackingResult, TrackState


def _track(track_id: int = 12) -> Track:
    now = utc_now()
    timeline = Timeline(
        first_seen=now, last_seen=now, first_frame=0, last_frame=0, history_size=10
    )
    return Track(
        track_id=track_id,
        camera_id=1,
        bbox=(10, 20, 50, 220),
        score=0.88,
        timeline=timeline,
        class_name="person",
        velocity=(2.0, -1.0),
        speed=0.02,
        speed_px=2.24,
        direction="LEFT",
        current_roi_id="desk_03",
        current_roi_name="Desk_03",
        status=TrackState.TRACKING,
    )


class TestTrackDTO:
    """Test serialize Track."""

    def test_to_dict_schema(self) -> None:
        """DTO có đủ field theo yêu cầu."""
        d = _track().to_dict()
        assert d["track_id"] == 12
        assert d["class"] == "person"
        assert d["bbox"] == [10.0, 20.0, 50.0, 220.0]
        assert d["center"] == [30.0, 120.0]
        assert d["direction"] == "LEFT"
        assert d["roi"] == "Desk_03"
        assert d["status"] == "TRACKING"
        assert "speed" in d

    def test_detail_dict_has_timeline(self) -> None:
        """Detail có timeline."""
        d = _track().to_detail_dict()
        assert "timeline" in d
        assert "roi_history" in d["timeline"]


class TestTrackingResultDTO:
    """Test serialize TrackingResult."""

    def test_to_dict(self) -> None:
        result = TrackingResult(
            camera_id=2,
            frame_id=100,
            timestamp=utc_now(),
            tracks=[_track(1), _track(2)],
            processing_time_ms=3.5,
        )
        d = result.to_dict()
        assert d["camera_id"] == 2
        assert d["frame_id"] == 100
        assert d["count"] == 2
        assert len(d["tracks"]) == 2
        assert d["processing_time_ms"] == 3.5

    def test_empty_result(self) -> None:
        result = TrackingResult(camera_id=1, frame_id=0, timestamp=utc_now())
        assert result.count == 0
        assert result.to_dict()["tracks"] == []
