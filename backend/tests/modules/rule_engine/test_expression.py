"""Unit test — expression operators."""

from __future__ import annotations

import pytest

from app.modules.rule_engine.exceptions import ExpressionError
from app.modules.rule_engine.expression import evaluate_operator


def test_basic_operators():
    assert evaluate_operator("==", True, True)
    assert evaluate_operator("!=", 1, 2)
    assert evaluate_operator(">", 11, 10)
    assert evaluate_operator(">=", 10, 10)
    assert evaluate_operator("<", 5, 10)
    assert evaluate_operator("<=", 10, 10)


def test_in_contains():
    assert evaluate_operator("in", "A", ["A", "B"])
    assert evaluate_operator("not_in", "C", ["A", "B"])
    assert evaluate_operator("contains", [1, 2, 3], 2)


def test_none_numeric_returns_false():
    assert evaluate_operator(">", None, 10) is False
    assert evaluate_operator("<", None, 10) is False


def test_unknown_operator_raises():
    with pytest.raises(ExpressionError):
        evaluate_operator("~=", 1, 1)
