"""
Rule validator — kiểm tra tính hợp lệ của Rule trước khi nạp/chạy.
"""

from __future__ import annotations

from typing import Any

from app.modules.rule_engine.condition.nodes import (
    ConditionNode,
    GroupCondition,
    LeafCondition,
)
from app.modules.rule_engine.exceptions import (
    ExpressionError,
    InvalidRuleError,
    MissingParameterError,
)
from app.modules.rule_engine.expression.operators import OPERATORS
from app.modules.rule_engine.rule_parser.rule import Rule

_KNOWN_FACTS = {
    "phone_detected",
    "hand_near_phone",
    "phone_person_near",
    "looking_phone",
    "looking_monitor",
    "head_down",
    "head_direction",
    "head_angle",
    "movement_speed",
    "stationary",
    "stationary_time",
    "low_motion",
    "sitting",
    "hand_on_desk",
    "hand_near_face",
    "working",
    "in_roi",
    "roi",
    "away_from_desk",
    "food_visible",
    "food_near_mouth",
    "person_count",
    "nearest_person_distance",
    "has_nearby_person",
}


def _validate_node(node: ConditionNode) -> None:
    """Kiểm tra đệ quy một nút điều kiện."""
    if isinstance(node, LeafCondition):
        if node.operator not in OPERATORS:
            raise ExpressionError(f"Toán tử không hỗ trợ: {node.operator}")
        if node.type != "duration" and node.type not in _KNOWN_FACTS:
            raise InvalidRuleError(f"Fact không xác định: {node.type}")
        if node.type != "duration" and node.value is None:
            raise MissingParameterError(f"value cho {node.type}")
    elif isinstance(node, GroupCondition):
        if node.operator.upper() not in {"AND", "OR", "NOT"}:
            raise InvalidRuleError(f"Toán tử nhóm không hợp lệ: {node.operator}")
        if not node.conditions:
            raise InvalidRuleError("Group không có điều kiện con.")
        for child in node.conditions:
            _validate_node(child)
    else:  # pragma: no cover
        raise InvalidRuleError("Loại nút điều kiện không hợp lệ.")


def validate_rule(rule: Rule) -> None:
    """
    Validate một Rule.

    Raises:
        InvalidRuleError / MissingParameterError / ExpressionError.
    """
    if not rule.id:
        raise MissingParameterError("id")
    if rule.condition is None:
        raise MissingParameterError("conditions")
    _validate_node(rule.condition)


def is_valid_rule(rule: Rule) -> bool:
    """True nếu rule hợp lệ (không raise)."""
    try:
        validate_rule(rule)
        return True
    except Exception:
        return False


def known_facts() -> set[str]:
    """Tập fact mà validator chấp nhận."""
    return set(_KNOWN_FACTS)
