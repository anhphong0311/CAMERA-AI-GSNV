"""Unit test — rule validator."""

from __future__ import annotations

import pytest

from app.modules.rule_engine.condition import GroupCondition, LeafCondition
from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.exceptions import ExpressionError, InvalidRuleError
from app.modules.rule_engine.rule_parser.rule import Rule
from app.modules.rule_engine.rule_validator import is_valid_rule, validate_rule


def _rule(condition) -> Rule:
    return Rule(id="R", name="R", condition=condition, severity=Severity.LOW)


def test_valid_rule():
    rule = _rule(
        GroupCondition(
            "AND",
            [
                LeafCondition("phone_detected", "==", True),
                LeafCondition("duration", ">", 10),
            ],
        )
    )
    validate_rule(rule)
    assert is_valid_rule(rule)


def test_unknown_fact_invalid():
    rule = _rule(GroupCondition("AND", [LeafCondition("banana", "==", True)]))
    with pytest.raises(InvalidRuleError):
        validate_rule(rule)


def test_bad_operator_invalid():
    rule = _rule(GroupCondition("AND", [LeafCondition("stationary", "~=", True)]))
    with pytest.raises(ExpressionError):
        validate_rule(rule)


def test_empty_group_invalid():
    rule = _rule(GroupCondition("AND", []))
    assert not is_valid_rule(rule)
