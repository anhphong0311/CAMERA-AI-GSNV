"""
Unit test — BehaviorFeatureDTO / BehaviorResult serialization.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.behavior.models import (
    BehaviorFeatureDTO,
    BehaviorResult,
    HeadFeature,
)


def test_dto_to_dict_has_all_sections():
    dto = BehaviorFeatureDTO(track_id=15, timestamp=datetime.now(timezone.utc))
    dto.head = HeadFeature(direction="DOWN", angle=28.0, available=True)
    d = dto.to_dict()
    for key in (
        "track_id",
        "timestamp",
        "head",
        "body",
        "hand",
        "gaze",
        "motion",
        "phone_feature",
        "food_feature",
        "chair_feature",
        "temporal_feature",
    ):
        assert key in d
    assert d["head"]["direction"] == "DOWN"
    assert d["track_id"] == 15


def test_result_to_dict():
    res = BehaviorResult(
        camera_id=1,
        frame_id=2,
        timestamp=datetime.now(timezone.utc),
        features=[
            BehaviorFeatureDTO(track_id=1, timestamp=datetime.now(timezone.utc))
        ],
    )
    d = res.to_dict()
    assert d["count"] == 1
    assert d["camera_id"] == 1
    assert len(d["features"]) == 1
