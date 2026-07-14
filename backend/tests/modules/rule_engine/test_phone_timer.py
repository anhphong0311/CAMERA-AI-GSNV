"""Tests — Phone timer gap reset in RuleExecutor."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.rule_engine.condition.nodes import GroupCondition, LeafCondition
from app.modules.rule_engine.rule_executor.executor import RuleExecutor
from app.modules.rule_engine.rule_parser.rule import Rule
from app.modules.rule_engine.state.rule_state import RuleState
from app.modules.rule_engine.event.severity import Severity

BASE = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)


def _phone_rule() -> Rule:
    return Rule(
        id="PHONE_USAGE",
        name="Phone",
        severity=Severity.HIGH,
        condition=GroupCondition(
            operator="AND",
            conditions=[
                LeafCondition(type="phone_detected", operator="==", value=True),
                LeafCondition(type="hand_near_phone", operator="==", value=True),
                LeafCondition(type="duration", operator=">", value=10),
            ],
        ),
    )


def test_phone_timer_gap_does_not_reset_within_2s():
    executor = RuleExecutor()
    rule = _phone_rule()
    state = RuleState(rule_id=rule.id, track_id=1, camera_id=1)
    facts = {"phone_detected": True, "hand_near_phone": True}

    for i in range(10):
        r = executor.execute(rule, facts, state, BASE + timedelta(seconds=i), 1.0, gap_reset_seconds=2.0)
        assert r.base_active is True

    # 1.5s gap — timer continues
    r = executor.execute(
        rule,
        {"phone_detected": False, "hand_near_phone": False},
        state,
        BASE + timedelta(seconds=11),
        1.5,
        gap_reset_seconds=2.0,
    )
    assert state.active_seconds >= 10
    assert r.fired is True


def test_phone_timer_resets_after_2s_gap():
    executor = RuleExecutor()
    rule = _phone_rule()
    state = RuleState(rule_id=rule.id, track_id=1, camera_id=1)
    facts = {"phone_detected": True, "hand_near_phone": True}

    for i in range(5):
        executor.execute(rule, facts, state, BASE + timedelta(seconds=i), 1.0, gap_reset_seconds=2.0)

    executor.execute(
        rule,
        {"phone_detected": False, "hand_near_phone": False},
        state,
        BASE + timedelta(seconds=8),
        3.0,
        gap_reset_seconds=2.0,
    )
    assert state.active_since is None
    assert state.lifecycle == "WAITING"
