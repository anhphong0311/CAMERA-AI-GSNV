"""Tests for detection_result_to_dashboard serializer."""

from datetime import datetime, timezone

from app.modules.ai.models import BoundingBox, Detection, DetectionResult
from app.modules.behavior.models import BehaviorFeatureDTO, BehaviorResult, HandFeature, PhoneFeature
from app.modules.realtime.detection_serializer import detection_result_to_dashboard


def test_detection_result_to_dashboard_normalized_bbox():
    det = Detection("person", 0.91, BoundingBox(100, 50, 300, 450), class_id=0)
    result = DetectionResult(
        camera_id=1,
        frame_id=10,
        timestamp=datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
        objects=[det],
        inference_time_ms=50.0,
        width=1920,
        height=1080,
    )
    payload = detection_result_to_dashboard(result)
    assert payload["camera_id"] == 1
    assert payload["fps"] == 20.0
    assert len(payload["objects"]) == 1
    obj = payload["objects"][0]
    assert obj["label"] == "person"
    assert obj["bbox"] == [
        round(100 / 1920, 4),
        round(50 / 1080, 4),
        round(200 / 1920, 4),
        round(400 / 1080, 4),
    ]


def test_phone_interaction_flag_on_dashboard():
    person = Detection("person", 0.9, BoundingBox(100, 140, 180, 360), class_id=0)
    phone = Detection("phone", 0.8, BoundingBox(115, 257, 135, 277), class_id=67)
    result = DetectionResult(
        camera_id=1,
        frame_id=1,
        timestamp=datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
        objects=[person, phone],
        width=640,
        height=480,
    )
    behavior = BehaviorResult(
        camera_id=1,
        frame_id=1,
        timestamp=result.timestamp,
        features=[
            BehaviorFeatureDTO(
                track_id=3,
                timestamp=result.timestamp,
                hand=HandFeature(
                    near_phone=True,
                    available=True,
                    left_position=(125.0, 267.0),
                ),
                phone_feature=PhoneFeature(visible=True),
            )
        ],
    )
    payload = detection_result_to_dashboard(result, behavior=behavior)
    assert payload["phone_interaction"] is True
    phone_objs = [o for o in payload["objects"] if o["label"] == "phone"]
    assert len(phone_objs) == 1
    assert phone_objs[0]["interacting"] is True


def test_desk_phone_not_shown_on_dashboard():
    """Súng quét mã trên bàn không được hiển thị như điện thoại."""
    person = Detection("person", 0.9, BoundingBox(100, 140, 180, 360), class_id=0)
    desk_scanner = Detection("phone", 0.75, BoundingBox(40, 340, 90, 380), class_id=67)
    result = DetectionResult(
        camera_id=1,
        frame_id=1,
        timestamp=datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
        objects=[person, desk_scanner],
        width=640,
        height=480,
    )
    payload = detection_result_to_dashboard(result)
    assert [o for o in payload["objects"] if o["label"] == "phone"] == []
