"""Unit test — cooldown & duplicate filter."""

from __future__ import annotations

from tests.modules.rule_engine.conftest import at

from app.modules.rule_engine.cache import CooldownCache, DuplicateFilter


def test_cooldown_active_then_expire():
    cd = CooldownCache()
    cd.start("PHONE_USAGE", 1, at(0), 300)
    assert cd.active("PHONE_USAGE", 1, at(100))
    assert not cd.active("PHONE_USAGE", 1, at(301))


def test_cooldown_cleanup():
    cd = CooldownCache()
    cd.start("R", 1, at(0), 10)
    assert cd.cleanup(at(20)) == 1


def test_duplicate_within_window():
    df = DuplicateFilter(window_seconds=300)
    df.record("R", 1, at(0))
    assert df.is_duplicate("R", 1, at(100))
    assert not df.is_duplicate("R", 1, at(400))


def test_duplicate_cleanup():
    df = DuplicateFilter(window_seconds=100)
    df.record("R", 1, at(0))
    assert df.cleanup(at(200)) == 1
