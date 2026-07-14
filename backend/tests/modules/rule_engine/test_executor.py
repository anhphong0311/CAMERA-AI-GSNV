"""Unit test — RuleExecutor (base_active, timer, fired via duration)."""

from __future__ import annotations

from tests.modules.rule_engine.conftest import at

from app.modules.rule_engine.condition import GroupCondition, LeafCondition
from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.rule_executor import RuleExecutor
from app.modules.rule_engine.rule_parser.rule import Rule
from app.modules.rule_engine.state.rule_state import RuleState


def _phone_rule() -> Rule:
    cond = GroupCondition(
        "AND",
        [
            LeafCondition("phone_detected", "==", True),
            LeafCondition("duration", ">", 10),
        ],
    )
    return Rule(id="PHONE_USAGE", name="Phone", condition=cond, severity=Severity.HIGH)


def test_executor_duration_accumulates_and_fires():
    rule = _phone_rule()
    executor = RuleExecutor()
    state = RuleState("PHONE_USAGE", 1, 1)
    facts = {"phone_detected": True}

    times = [0, 6, 12]
    results = []
    for t in times:
        dt = (at(t) - state.last_ts).total_seconds() if state.last_ts else 0.0
        results.append(executor.execute(rule, facts, state, at(t), dt))

    assert results[0].base_active and not results[0].fired  # 0s
    assert not results[1].fired  # 6s
    assert results[2].fired  # 12s > 10


def test_executor_resets_when_inactive():
    rule = _phone_rule()
    executor = RuleExecutor()
    state = RuleState("PHONE_USAGE", 1, 1)

    executor.execute(rule, {"phone_detected": True}, state, at(0), 0.0)
    executor.execute(rule, {"phone_detected": True}, state, at(20), 20.0)
    r = executor.execute(rule, {"phone_detected": False}, state, at(21), 1.0)
    assert r.base_active is False
    assert state.active_seconds == 0.0
