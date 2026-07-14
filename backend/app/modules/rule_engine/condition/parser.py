"""
Condition parser — dựng cây ConditionNode từ dict (JSON/YAML).

Hỗ trợ:
- list → nhóm AND ngầm định.
- dict có "operator" (+ "conditions") → GroupCondition.
- dict leaf {type, operator, value} → LeafCondition.
"""

from __future__ import annotations

from typing import Any, List

from app.modules.rule_engine.condition.nodes import (
    ConditionNode,
    GroupCondition,
    LeafCondition,
)
from app.modules.rule_engine.exceptions import (
    CircularRuleError,
    InvalidRuleError,
    MissingParameterError,
)

_MAX_DEPTH = 10
_GROUP_OPS = {"AND", "OR", "NOT"}


def parse_conditions(raw: Any, depth: int = 0) -> ConditionNode:
    """
    Parse cấu trúc điều kiện thành cây.

    Args:
        raw: list hoặc dict.
        depth: độ sâu hiện tại (chống lồng vô hạn).

    Returns:
        ConditionNode.

    Raises:
        CircularRuleError: lồng quá sâu.
        InvalidRuleError / MissingParameterError: cấu trúc sai.
    """
    if depth > _MAX_DEPTH:
        raise CircularRuleError(f"Điều kiện lồng vượt {_MAX_DEPTH} cấp.")

    if isinstance(raw, list):
        return GroupCondition(
            operator="AND",
            conditions=[parse_conditions(item, depth + 1) for item in raw],
        )

    if isinstance(raw, dict):
        operator = raw.get("operator")
        # Group khi có "conditions" và operator là AND/OR/NOT
        if "conditions" in raw and str(operator).upper() in _GROUP_OPS:
            children_raw = raw.get("conditions") or []
            if not isinstance(children_raw, list):
                raise InvalidRuleError("'conditions' của group phải là list.")
            children: List[ConditionNode] = [
                parse_conditions(item, depth + 1) for item in children_raw
            ]
            return GroupCondition(operator=str(operator).upper(), conditions=children)

        # Leaf
        if "type" not in raw:
            raise MissingParameterError("type")
        if "operator" not in raw:
            raise MissingParameterError("operator")
        if "value" not in raw and raw["type"] != "duration":
            raise MissingParameterError("value")
        return LeafCondition(
            type=str(raw["type"]),
            operator=str(raw["operator"]),
            value=raw.get("value"),
        )

    raise InvalidRuleError(f"Cấu trúc điều kiện không hợp lệ: {raw!r}")
