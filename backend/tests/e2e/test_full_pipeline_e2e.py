"""
End-to-End pipeline test (Sprint 12 QA).

Camera (mock frame) → Detection → Tracking → Behavior → Rule → Event.

Không dùng GPU/RTSP thật — kiểm tra luồng DTO giữa các module.
"""

from __future__ import annotations

from app.modules.behavior.config import BehaviorConfig
from app.modules.event.repositories.store import InMemoryEventStore
from app.modules.event.schemas.records import EventRecord
from app.modules.rule_engine.services import RuleService
from app.modules.tracking.services.tracking_service import TrackingService
from tests.modules.behavior.conftest import make_pose
from tests.modules.rule_engine.conftest import at, make_dto, make_behavior_result, make_tracking
from tests.modules.tracking.conftest import make_detection_result, tracking_config


def test_e2e_phone_usage_to_event_store():
    """UAT: phone visible → rule → event stored."""
    rule_svc = RuleService()
    rule_svc.load_rules_file()
    store = InMemoryEventStore()
    events_created = []

    for i, t in enumerate([0, 5, 12, 18]):
        dto = make_dto(
            1,
            ts=at(t),
            phone_visible=True,
            hand_near_phone=True,
            looking="PHONE",
        )
        behavior = make_behavior_result(1, i, [dto], ts=at(t))
        tracking = make_tracking(1, i, [(1, (0, 0, 100, 200), "desk")], ts=at(t))
        events_created.extend(rule_svc.process(None, tracking, behavior))

    assert len(events_created) >= 1
    ev = events_created[0]
    store.save(
        EventRecord(
            event_id=ev.event_id,
            camera_id=ev.camera_id,
            track_id=ev.track_id,
            rule_id=ev.rule_id,
            event_type=ev.event_type,
            severity=ev.severity.value,
            confidence=ev.confidence,
            duration=ev.duration,
            start_time=ev.start_time,
            end_time=ev.end_time,
            metadata=ev.metadata,
        )
    )
    assert store.get(ev.event_id).rule_id == ev.rule_id


def test_e2e_detection_to_tracking(tracking_config):
    """DetectionResult → TrackingService → tracks."""
    svc = TrackingService(tracking_config)
    dr = make_detection_result(1, 0, [(10, 10, 100, 200), (200, 50, 300, 250)])
    result = svc.process(dr)
    assert result.camera_id == 1
    assert result.count >= 1


def test_e2e_tracking_to_behavior():
    """Tracking + Pose → BehaviorService → BehaviorResult."""
    from datetime import datetime, timezone

    from app.modules.ai.models import BoundingBox, Detection, DetectionResult
    from app.modules.behavior.services import BehaviorService
    from app.modules.tracking.config import TrackingConfig

    tracking_svc = TrackingService(TrackingConfig())
    behavior_svc = BehaviorService(BehaviorConfig())
    base = datetime.now(timezone.utc)
    dr = DetectionResult(
        camera_id=1,
        frame_id=0,
        timestamp=base,
        objects=[Detection("person", 0.95, BoundingBox(10, 10, 110, 210), 0)],
        width=640,
        height=480,
    )
    tr = tracking_svc.process(dr)
    poses = [make_pose((10, 10, 110, 210))]
    result = behavior_svc.process(None, tr, detections=dr.objects, poses=poses)
    assert result.camera_id == 1
    assert result.count >= 1


def test_e2e_regression_all_modules_importable():
    """Regression: mọi module core import được."""
    import app.modules.admin  # noqa: F401
    import app.modules.ai  # noqa: F401
    import app.modules.behavior  # noqa: F401
    import app.modules.camera  # noqa: F401
    import app.modules.event  # noqa: F401
    import app.modules.ops  # noqa: F401
    import app.modules.performance  # noqa: F401
    import app.modules.realtime  # noqa: F401
    import app.modules.rule_engine  # noqa: F401
    import app.modules.tracking  # noqa: F401
