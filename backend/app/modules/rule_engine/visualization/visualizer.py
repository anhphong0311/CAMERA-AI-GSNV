"""
Visualization — biểu diễn Rule Flow / Condition Tree / Event Lifecycle / Timeline
dưới dạng dict (debug/frontend). KHÔNG phụ thuộc render engine.
"""

from __future__ import annotations

from typing import Any, Dict

from app.modules.rule_engine.rule_parser.rule import Rule


def rule_flow() -> Dict[str, Any]:
    """Sơ đồ pipeline Rule Engine."""
    return {
        "stages": [
            "DetectionResult",
            "TrackingResult",
            "BehaviorFeatureDTO",
            "Facts",
            "Condition",
            "Expression",
            "Evaluation",
            "Event",
            "Action",
            "AlertQueue",
        ]
    }


def condition_tree(rule: Rule) -> Dict[str, Any]:
    """Cây điều kiện của một rule."""
    return {
        "rule_id": rule.id,
        "name": rule.name,
        "enabled": rule.enabled,
        "severity": rule.severity.value,
        "priority": rule.priority,
        "tree": rule.condition.to_dict(),
    }


def event_lifecycle() -> Dict[str, Any]:
    """Sơ đồ vòng đời event."""
    return {
        "states": ["NEW", "ACTIVE", "CONFIRMED", "ENDED", "IGNORED"],
        "flow": ["Created", "Candidate", "Confirmed", "Alerted", "Resolved"],
        "transitions": {
            "NEW": ["ACTIVE", "CONFIRMED", "IGNORED"],
            "ACTIVE": ["CONFIRMED", "ENDED", "IGNORED"],
            "CONFIRMED": ["ENDED"],
            "ENDED": [],
            "IGNORED": [],
        },
    }
