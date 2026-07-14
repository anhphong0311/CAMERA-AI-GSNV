"""Unit test — RuleService (CRUD, enable/disable, statistics)."""

from __future__ import annotations

import pytest

from app.modules.rule_engine.exceptions import RuleNotFoundError


def test_service_seeds_rules(service):
    ids = {r.id for r in service.list_rules()}
    assert "PHONE_USAGE" in ids
    assert len(service.list_rules()) >= 6


def test_service_add_get_update_delete(service):
    raw = {
        "id": "CUSTOM_TEST",
        "name": "Custom",
        "severity": "LOW",
        "conditions": [
            {"type": "stationary", "operator": "==", "value": True},
            {"type": "duration", "operator": ">", "value": 5},
        ],
    }
    rule = service.add_rule(raw)
    assert rule.id == "CUSTOM_TEST"
    assert service.get_rule("CUSTOM_TEST") is not None

    raw["severity"] = "HIGH"
    updated = service.update_rule("CUSTOM_TEST", raw)
    assert updated.severity.value == "HIGH"

    service.delete_rule("CUSTOM_TEST")
    with pytest.raises(RuleNotFoundError):
        service.get_rule("CUSTOM_TEST")


def test_service_enable_disable(service):
    service.set_enabled("PHONE_USAGE", False)
    assert service.get_rule("PHONE_USAGE").enabled is False
    service.set_enabled("PHONE_USAGE", True)
    assert service.get_rule("PHONE_USAGE").enabled is True


def test_service_statistics(service):
    stats = service.statistics()
    assert stats["rules"] >= 6
    assert "events" in stats
    assert "alert_queue" in stats
