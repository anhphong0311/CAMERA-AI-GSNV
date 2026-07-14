"""
Condition tree — Leaf / Group (AND/OR/NOT/GROUP), hỗ trợ nested condition.

Leaf đặc biệt type="duration" so với thời gian điều kiện nền được giữ liên tục.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional, Set

from app.modules.rule_engine.expression.operators import evaluate_operator

DURATION_TYPE = "duration"


class ConditionNode(ABC):
    """Nút điều kiện (Composite pattern)."""

    @abstractmethod
    def evaluate(self, facts: dict[str, Any], duration_seconds: Optional[float]) -> bool:
        """
        Đánh giá điều kiện.

        Args:
            facts: dict fact hiện tại.
            duration_seconds: thời gian điều kiện nền đã giữ (None = bỏ qua leaf duration).
        """

    @abstractmethod
    def required_facts(self) -> Set[str]:
        """Tập fact mà cây tham chiếu (trừ duration)."""

    @abstractmethod
    def has_duration(self) -> bool:
        """Cây có chứa leaf duration không."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize (dùng cho API + visualization)."""

    def duration_satisfied(self, duration_seconds: float) -> bool:
        """Chỉ kiểm tra leaf duration (grace period phone timer)."""
        return self.evaluate({}, duration_seconds=duration_seconds)


@dataclass
class LeafCondition(ConditionNode):
    """Điều kiện lá: fact operator value."""

    type: str
    operator: str
    value: Any

    def evaluate(self, facts: dict[str, Any], duration_seconds: Optional[float]) -> bool:
        if self.type == DURATION_TYPE:
            if duration_seconds is None:
                return True
            return evaluate_operator(self.operator, duration_seconds, self.value)
        if self.type not in facts:
            return False
        return evaluate_operator(self.operator, facts.get(self.type), self.value)

    def required_facts(self) -> Set[str]:
        return set() if self.type == DURATION_TYPE else {self.type}

    def has_duration(self) -> bool:
        return self.type == DURATION_TYPE

    def duration_satisfied(self, duration_seconds: float) -> bool:
        if self.type == DURATION_TYPE:
            return evaluate_operator(self.operator, duration_seconds, self.value)
        return True

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "operator": self.operator, "value": self.value}


@dataclass
class GroupCondition(ConditionNode):
    """Nhóm điều kiện: AND / OR / NOT."""

    operator: str  # AND | OR | NOT
    conditions: List[ConditionNode] = field(default_factory=list)

    def evaluate(self, facts: dict[str, Any], duration_seconds: Optional[float]) -> bool:
        op = self.operator.upper()
        if not self.conditions:
            return True
        results = (c.evaluate(facts, duration_seconds) for c in self.conditions)
        if op == "AND":
            return all(results)
        if op == "OR":
            return any(results)
        if op == "NOT":
            # NOT phủ định AND của các con (thường 1 con)
            return not all(c.evaluate(facts, duration_seconds) for c in self.conditions)
        return all(results)

    def required_facts(self) -> Set[str]:
        facts: Set[str] = set()
        for c in self.conditions:
            facts |= c.required_facts()
        return facts

    def has_duration(self) -> bool:
        return any(c.has_duration() for c in self.conditions)

    def duration_satisfied(self, duration_seconds: float) -> bool:
        op = self.operator.upper()
        if not self.conditions:
            return True
        results = (c.duration_satisfied(duration_seconds) for c in self.conditions)
        if op == "AND":
            return all(results)
        if op == "OR":
            return any(results)
        if op == "NOT":
            return not all(
                c.duration_satisfied(duration_seconds) for c in self.conditions
            )
        return all(results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator.upper(),
            "conditions": [c.to_dict() for c in self.conditions],
        }
