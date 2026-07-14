"""Unit test — condition tree (Leaf/Group AND/OR/NOT, nested, duration) + parser."""

from __future__ import annotations

import pytest

from app.modules.rule_engine.condition import (
    GroupCondition,
    LeafCondition,
    parse_conditions,
)
from app.modules.rule_engine.exceptions import (
    CircularRuleError,
    MissingParameterError,
)


def test_leaf_eval_fact():
    leaf = LeafCondition("phone_detected", "==", True)
    assert leaf.evaluate({"phone_detected": True}, None)
    assert not leaf.evaluate({"phone_detected": False}, None)


def test_leaf_missing_fact_false():
    leaf = LeafCondition("phone_detected", "==", True)
    assert leaf.evaluate({}, None) is False


def test_duration_leaf():
    leaf = LeafCondition("duration", ">", 10)
    assert leaf.evaluate({}, None) is True  # None → bỏ qua
    assert leaf.evaluate({}, 5) is False
    assert leaf.evaluate({}, 15) is True


def test_group_and_or_not():
    a = LeafCondition("x", "==", True)
    b = LeafCondition("y", "==", True)
    grp_and = GroupCondition("AND", [a, b])
    grp_or = GroupCondition("OR", [a, b])
    grp_not = GroupCondition("NOT", [a])
    facts = {"x": True, "y": False}
    assert grp_and.evaluate(facts, None) is False
    assert grp_or.evaluate(facts, None) is True
    assert grp_not.evaluate(facts, None) is False
    assert grp_not.evaluate({"x": False}, None) is True


def test_parse_list_is_and():
    node = parse_conditions(
        [
            {"type": "phone_detected", "operator": "==", "value": True},
            {"type": "duration", "operator": ">", "value": 10},
        ]
    )
    assert isinstance(node, GroupCondition)
    assert node.operator == "AND"
    assert node.has_duration()


def test_parse_nested_group():
    node = parse_conditions(
        {
            "operator": "OR",
            "conditions": [
                {"type": "phone_detected", "operator": "==", "value": True},
                {
                    "operator": "AND",
                    "conditions": [
                        {"type": "head_down", "operator": "==", "value": True},
                        {"type": "low_motion", "operator": "==", "value": True},
                    ],
                },
            ],
        }
    )
    assert node.operator == "OR"
    assert "head_down" in node.required_facts()


def test_parse_missing_type_raises():
    with pytest.raises(MissingParameterError):
        parse_conditions({"operator": "==", "value": True})


def test_parse_too_deep_raises():
    node = {"type": "x", "operator": "==", "value": 1}
    for _ in range(12):
        node = {"operator": "AND", "conditions": [node]}
    with pytest.raises(CircularRuleError):
        parse_conditions(node)
