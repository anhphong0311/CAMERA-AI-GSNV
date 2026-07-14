"""
Rule parser — dựng Rule từ dict / JSON / YAML.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

import yaml

from app.modules.rule_engine.condition.parser import parse_conditions
from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.exceptions import InvalidRuleError, MissingParameterError
from app.modules.rule_engine.rule_parser.rule import Rule


def parse_rule(raw: dict[str, Any]) -> Rule:
    """
    Parse một dict rule thành Rule.

    Raises:
        MissingParameterError / InvalidRuleError.
    """
    if not isinstance(raw, dict):
        raise InvalidRuleError("Rule phải là object/dict.")
    if "id" not in raw:
        raise MissingParameterError("id")
    if "conditions" not in raw:
        raise MissingParameterError("conditions")

    condition = parse_conditions(raw["conditions"])
    return Rule(
        id=str(raw["id"]),
        name=str(raw.get("name", raw["id"])),
        condition=condition,
        enabled=bool(raw.get("enabled", True)),
        severity=Severity.from_str(str(raw.get("severity", "INFO"))),
        priority=int(raw.get("priority", 3)),
        cooldown=(
            float(raw["cooldown"]) if raw.get("cooldown") is not None else None
        ),
        actions=list(raw.get("actions", ["alert"])),
        description=str(raw.get("description", "")),
        category=raw.get("category"),
    )


def parse_rules(raw_list: Any) -> List[Rule]:
    """Parse danh sách rule."""
    if not isinstance(raw_list, list):
        raise InvalidRuleError("Danh sách rule phải là list.")
    return [parse_rule(r) for r in raw_list]


def parse_rules_from_json(text: str) -> List[Rule]:
    """Parse rule từ chuỗi JSON (một rule hoặc list)."""
    data = json.loads(text)
    if isinstance(data, dict):
        return [parse_rule(data)]
    return parse_rules(data)


def load_rules_from_file(path: str | Path) -> List[Rule]:
    """
    Nạp rule từ file .yaml/.yml/.json.
    """
    p = Path(path)
    if not p.exists():
        raise InvalidRuleError(f"Không tìm thấy file rule: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return parse_rules_from_json(text)
    data = yaml.safe_load(text) or []
    if isinstance(data, dict):
        # cho phép {rules: [...]}
        data = data.get("rules", [data])
    return parse_rules(data)
