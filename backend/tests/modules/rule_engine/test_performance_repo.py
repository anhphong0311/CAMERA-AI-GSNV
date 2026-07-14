"""Unit test — performance score + repositories."""

from __future__ import annotations

import pytest

from tests.modules.rule_engine.conftest import at

from app.modules.rule_engine.condition import GroupCondition, LeafCondition
from app.modules.rule_engine.event.event import BehaviorEventDTO
from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.exceptions import DuplicateRuleError, RuleNotFoundError
from app.modules.rule_engine.repositories import EventRepository, RuleRepository
from app.modules.rule_engine.rule_engine.performance import PerformanceScoreCalculator
from app.modules.rule_engine.rule_parser.rule import Rule
from app.modules.rule_engine.state.event_state import EventState


def test_performance_score_penalizes_phone():
    calc = PerformanceScoreCalculator({"phone": 1.0})
    for _ in range(10):
        calc.update(1, 1, 1.0, {"phone": True}, working=False)
    assert calc.score(1) < 50.0


def test_performance_full_when_working():
    calc = PerformanceScoreCalculator({"phone": 1.0})
    for _ in range(10):
        calc.update(1, 1, 1.0, {"phone": False}, working=True)
    assert calc.score(1) == 100.0


def test_performance_default_score_no_data():
    calc = PerformanceScoreCalculator({"phone": 1.0})
    assert calc.score(99) == 100.0


def _rule(rid: str = "R") -> Rule:
    cond = GroupCondition("AND", [LeafCondition("stationary", "==", True)])
    return Rule(id=rid, name=rid, condition=cond, severity=Severity.LOW)


def test_rule_repository_duplicate_and_notfound():
    repo = RuleRepository()
    repo.add(_rule("A"))
    assert repo.get("A") is not None
    with pytest.raises(DuplicateRuleError):
        repo.add(_rule("A"))
    with pytest.raises(RuleNotFoundError):
        repo.delete("Z")


def test_rule_repository_enabled_sorted_by_priority():
    repo = RuleRepository()
    r1 = _rule("A")
    r1.priority = 3
    r2 = _rule("B")
    r2.priority = 1
    repo.add(r1)
    repo.add(r2)
    assert repo.enabled_rules()[0].id == "B"


def test_rule_repository_set_enabled():
    repo = RuleRepository()
    repo.add(_rule("A"))
    repo.set_enabled("A", False)
    assert repo.enabled_rules() == []


def test_event_repository_live_history():
    repo = EventRepository()
    ev = BehaviorEventDTO(
        camera_id=1,
        track_id=1,
        rule_id="PHONE_USAGE",
        event_type="PHONE_USAGE",
        severity=Severity.HIGH,
        start_time=at(0),
        state=EventState.CONFIRMED,
    )
    repo.add(ev)
    assert len(repo.live()) == 1
    assert len(repo.history(rule_id="PHONE_USAGE")) == 1
    repo.end(ev)
    assert len(repo.live()) == 0
    stats = repo.statistics()
    assert stats["total_events"] == 1
    assert stats["by_severity"]["HIGH"] == 1
