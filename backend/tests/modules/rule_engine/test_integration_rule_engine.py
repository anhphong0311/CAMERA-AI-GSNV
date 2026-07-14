"""
Integration test — Detection → Tracking → Behavior Feature → Rule Engine → Event.

Dùng DTO chuẩn giữa các module (không cần pose model / GPU).
Kiểm tra: event lifecycle, cooldown, performance score, alert queue, dọn state.
"""

from __future__ import annotations

from tests.modules.rule_engine.conftest import (
    at,
    make_behavior_result,
    make_dto,
    make_tracking,
)

from app.modules.rule_engine.services import RuleService
from app.modules.rule_engine.visualization import (
    condition_tree,
    event_lifecycle,
    rule_flow,
)


def test_full_pipeline_eating_event():
    service = RuleService()
    service.load_rules_file()

    created = []
    # EATING: food_visible + food_near_mouth + duration>60
    for i, t in enumerate([0, 30, 61, 70]):
        dto = make_dto(
            5,
            ts=at(t),
            cup_mouth=25.0,
            food_near_mouth=True,
            hand_near_face=True,
            body_in_roi=True,
        )
        behavior = make_behavior_result(2, i, [dto], ts=at(t))
        tracking = make_tracking(
            2, i, [(5, (10, 10, 110, 210), "desk")], ts=at(t)
        )
        created += service.process(None, tracking, behavior)

    assert any(e.rule_id == "EATING" for e in created)
    ev = next(e for e in created if e.rule_id == "EATING")
    assert ev.camera_id == 2
    assert ev.track_id == 5
    assert ev.duration > 60
    assert ev.severity.value == "LOW"
    assert 0.0 <= ev.confidence <= 1.0
    assert "facts" in ev.metadata


def test_pipeline_performance_and_alert_queue():
    service = RuleService()
    service.load_rules_file()
    for i, t in enumerate(range(0, 40, 6)):
        dto = make_dto(
            1, ts=at(t), phone_visible=True, hand_near_phone=True, looking="PHONE"
        )
        behavior = make_behavior_result(1, i, [dto], ts=at(t))
        tracking = make_tracking(1, i, [(1, (0, 0, 100, 200), "desk")], ts=at(t))
        service.process(None, tracking, behavior)

    reports = service.performance_reports()
    assert reports
    assert reports[0]["score"] <= 100.0
    # PHONE_USAGE alert ngay khi đủ duration
    assert service.alert_queue().total_pushed >= 1
    alert = service.alert_queue().peek_all()[0]
    assert alert.rule_id == "PHONE_USAGE"
    assert alert.start_time is not None

def test_pipeline_multi_track_independent():
    service = RuleService()
    service.load_rules_file()
    created = []
    for i, t in enumerate([0, 11, 22]):
        dtos = [
            make_dto(1, ts=at(t), head_direction="DOWN", movement_speed=0.1),
            make_dto(2, ts=at(t), phone_visible=True, hand_near_phone=True),
        ]
        behavior = make_behavior_result(1, i, dtos, ts=at(t))
        tracking = make_tracking(
            1,
            i,
            [(1, (0, 0, 100, 200), "desk"), (2, (300, 0, 400, 200), "desk")],
            ts=at(t),
        )
        created += service.process(None, tracking, behavior)
    rule_ids = {e.rule_id for e in created}
    assert "SLEEPING" in rule_ids


def test_visualization_outputs():
    service = RuleService()
    service.load_rules_file()
    assert "stages" in rule_flow()
    assert "states" in event_lifecycle()
    tree = condition_tree(service.get_rule("PHONE_USAGE"))
    assert tree["rule_id"] == "PHONE_USAGE"
    assert "tree" in tree


def test_no_state_leak_after_shutdown():
    service = RuleService()
    service.load_rules_file()
    dto = make_dto(1, ts=at(0), phone_visible=True, hand_near_phone=True)
    behavior = make_behavior_result(1, 0, [dto], ts=at(0))
    tracking = make_tracking(1, 0, [(1, (0, 0, 100, 200), "desk")], ts=at(0))
    service.process(None, tracking, behavior)
    service.shutdown()
    assert service.statistics()["cameras"] == 0
