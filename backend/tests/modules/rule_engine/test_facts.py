"""Unit test — FactExtractor (build_facts)."""

from __future__ import annotations

from tests.modules.rule_engine.conftest import make_dto

from app.modules.rule_engine.rule_engine.facts import build_facts, estimate_confidence
from app.modules.behavior.models import TrackView


def _track(roi=None):
    return TrackView(track_id=1, camera_id=1, bbox=(0, 0, 100, 200), current_roi_id=roi)


def test_facts_phone():
    dto = make_dto(1, phone_visible=True, hand_near_phone=True, looking="PHONE")
    facts = build_facts(dto, _track("desk"), 1, None, 2.0, 150.0)
    assert facts["phone_detected"] is True
    assert facts["hand_near_phone"] is True
    assert facts["looking_phone"] is True
    assert facts["in_roi"] is True
    assert facts["away_from_desk"] is False


def test_facts_low_motion_and_head_down():
    dto = make_dto(1, head_direction="DOWN", movement_speed=0.5)
    facts = build_facts(dto, _track("desk"), 1, None, 2.0, 150.0)
    assert facts["head_down"] is True
    assert facts["low_motion"] is True


def test_facts_away_when_outside_roi():
    dto = make_dto(1, body_in_roi=False)
    facts = build_facts(
        dto, _track(None), 1, None, 2.0, 150.0, desk_roi_configured=True
    )
    assert facts["in_roi"] is False
    assert facts["away_from_desk"] is True


def test_facts_not_away_when_visible_without_roi():
    """1 camera ≈ 1 bàn: người còn trong khung không tính rời chỗ."""
    dto = make_dto(1, body_in_roi=False)
    facts = build_facts(
        dto, _track(None), 1, None, 2.0, 150.0, desk_roi_configured=False
    )
    assert facts["away_from_desk"] is False


def test_facts_nearby_person():
    dto = make_dto(1)
    facts = build_facts(dto, _track("desk"), 2, 100.0, 2.0, 150.0)
    assert facts["person_count"] == 2
    assert facts["has_nearby_person"] is True


def test_facts_food_visible():
    dto = make_dto(1, cup_mouth=30.0, food_near_mouth=True)
    facts = build_facts(dto, _track("desk"), 1, None, 2.0, 150.0)
    assert facts["food_visible"] is True
    assert facts["food_near_mouth"] is True


def test_confidence_range():
    dto = make_dto(1)
    c = estimate_confidence(dto, _track("desk"))
    assert 0.0 <= c <= 1.0
