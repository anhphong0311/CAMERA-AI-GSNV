"""Unit test — RuleEngine event lifecycle, cooldown, duplicate filter."""

from __future__ import annotations

from tests.modules.rule_engine.conftest import (
    at,
    make_behavior_result,
    make_dto,
    make_tracking,
)

from app.modules.rule_engine.action import AlertQueue
from app.modules.rule_engine.config import (
    load_cooldown_config,
    load_rule_engine_config,
)
from app.modules.rule_engine.repositories import EventRepository, RuleRepository
from app.modules.rule_engine.rule_engine.engine import RuleEngine
from app.modules.rule_engine.rule_parser import load_rules_from_file
from app.modules.rule_engine.config import rules_config_path


def _build_engine(camera_id: int = 1):
    rule_repo = RuleRepository()
    for r in load_rules_from_file(rules_config_path()):
        rule_repo.upsert(r)
    event_repo = EventRepository()
    queue = AlertQueue()
    engine = RuleEngine(
        camera_id=camera_id,
        rule_repo=rule_repo,
        event_repo=event_repo,
        alert_queue=queue,
        config=load_rule_engine_config(),
        cooldown_config=load_cooldown_config(),
    )
    return engine, event_repo, queue


def _phone_frame(frame_id: int, t: float):
    dto = make_dto(
        1,
        ts=at(t),
        phone_visible=True,
        hand_near_phone=True,
        looking="PHONE",
        body_in_roi=True,
    )
    behavior = make_behavior_result(1, frame_id, [dto], ts=at(t))
    tracking = make_tracking(1, frame_id, [(1, (0, 0, 100, 200), "desk")], ts=at(t))
    return tracking, behavior


def test_phone_usage_fires_after_duration():
    engine, event_repo, queue = _build_engine()
    created_total = []
    for i, t in enumerate([0, 3, 6]):
        tracking, behavior = _phone_frame(i, t)
        created_total += engine.process(None, tracking, behavior)

    assert any(e.rule_id == "PHONE_USAGE" for e in created_total)
    # PHONE_USAGE gửi alert ngay khi đủ ngưỡng (không chờ cất máy)
    assert queue.size >= 1
    alert = queue.peek_all()[0]
    assert alert.rule_id == "PHONE_USAGE"
    assert alert.start_time is not None
    assert len(event_repo.live()) >= 1


def test_no_event_before_duration():
    engine, event_repo, _ = _build_engine()
    created = []
    for i, t in enumerate([0, 2]):
        tracking, behavior = _phone_frame(i, t)
        created += engine.process(None, tracking, behavior)
    assert not any(e.rule_id == "PHONE_USAGE" for e in created)


def test_duplicate_filter_blocks_second_event():
    engine, event_repo, _ = _build_engine()
    # frame 1: fire
    for i, t in enumerate([0, 3, 6]):
        tracking, behavior = _phone_frame(i, t)
        engine.process(None, tracking, behavior)
    # phone away → event ends, cooldown/duplicate starts
    dto = make_dto(1, ts=at(20), phone_visible=False)
    behavior = make_behavior_result(1, 3, [dto], ts=at(20))
    tracking = make_tracking(1, 3, [(1, (0, 0, 100, 200), "desk")], ts=at(20))
    engine.process(None, tracking, behavior)
    # re-satisfy within duplicate window → no new event
    created = []
    for i, t in enumerate([30, 34, 38], start=4):
        tr, bh = _phone_frame(i, t)
        created += engine.process(None, tr, bh)
    assert not any(e.rule_id == "PHONE_USAGE" for e in created)


def test_away_from_desk_alert_on_empty_desk():
    """AWAY_FROM_DESK (không ROI): bàn trống đủ lâu → alert ngay + ảnh empty desk."""
    engine, event_repo, queue = _build_engine()
    engine._desk_roi_cached = False  # 1 camera ≈ 1 bàn

    # Có người → không alert
    dto = make_dto(1, ts=at(0), body_in_roi=True)
    behavior = make_behavior_result(1, 0, [dto], ts=at(0))
    tracking = make_tracking(1, 0, [(1, (0, 0, 100, 200), None)], ts=at(0))
    engine.process(None, tracking, behavior)
    assert queue.size == 0

    # Bàn trống dần đủ >180s
    for i, t in enumerate([1, 90, 182], start=1):
        empty_behavior = make_behavior_result(1, i, [], ts=at(t))
        empty_tracking = make_tracking(1, i, [], ts=at(t))
        engine.process(None, empty_tracking, empty_behavior)

    assert queue.size >= 1
    alert = queue.peek_all()[0]
    assert alert.rule_id == "AWAY_FROM_DESK"
    assert alert.metadata.get("empty_desk") is True
    assert alert.start_time is not None


def test_away_from_desk_with_roi_alert_when_outside():
    """AWAY_FROM_DESK (có ROI): người ngoài ROI đủ lâu → alert ngay."""
    engine, event_repo, queue = _build_engine()
    engine._desk_roi_cached = True

    for i, t in enumerate([0, 90, 182]):
        dto = make_dto(1, ts=at(t), body_in_roi=False)
        behavior = make_behavior_result(1, i, [dto], ts=at(t))
        tracking = make_tracking(1, i, [(1, (500, 0, 600, 200), None)], ts=at(t))
        engine.process(None, tracking, behavior)

    assert queue.size >= 1
    assert queue.peek_all()[0].rule_id == "AWAY_FROM_DESK"


def test_sleeping_rule():
    engine, event_repo, _ = _build_engine()
    created = []
    for i, t in enumerate([0, 11, 22]):
        dto = make_dto(
            1,
            ts=at(t),
            head_direction="DOWN",
            movement_speed=0.2,
            motion_direction="STATIONARY",
        )
        behavior = make_behavior_result(1, i, [dto], ts=at(t))
        tracking = make_tracking(1, i, [(1, (0, 0, 100, 200), "desk")], ts=at(t))
        created += engine.process(None, tracking, behavior)
    assert any(e.rule_id == "SLEEPING" for e in created)

