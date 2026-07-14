"""Unit test — rule parser (dict/JSON/YAML/file)."""

from __future__ import annotations

import pytest

from app.modules.rule_engine.config import rules_config_path
from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.exceptions import MissingParameterError
from app.modules.rule_engine.rule_parser import (
    load_rules_from_file,
    parse_rule,
    parse_rules_from_json,
)


def test_parse_rule_dict():
    rule = parse_rule(
        {
            "id": "PHONE_USAGE",
            "name": "Phone Usage",
            "severity": "HIGH",
            "priority": 1,
            "conditions": [
                {"type": "phone_detected", "operator": "==", "value": True},
                {"type": "duration", "operator": ">", "value": 10},
            ],
        }
    )
    assert rule.id == "PHONE_USAGE"
    assert rule.severity == Severity.HIGH
    assert rule.category == "phone"
    assert rule.condition.has_duration()


def test_parse_rule_json():
    text = (
        '{"id":"IDLE","conditions":['
        '{"type":"stationary","operator":"==","value":true},'
        '{"type":"duration","operator":">","value":600}]}'
    )
    rules = parse_rules_from_json(text)
    assert len(rules) == 1
    assert rules[0].id == "IDLE"


def test_parse_rule_missing_conditions():
    with pytest.raises(MissingParameterError):
        parse_rule({"id": "X"})


def test_load_rules_yaml_file():
    rules = load_rules_from_file(rules_config_path())
    ids = {r.id for r in rules}
    assert {
        "PHONE_USAGE",
        "AWAY_FROM_DESK",
        "PRIVATE_TALKING",
        "EATING",
        "SLEEPING",
        "IDLE",
    } <= ids
