"""Unit test — temporal analysis + state store/machine."""

from __future__ import annotations

from tests.modules.rule_engine.conftest import at

from app.modules.rule_engine.state import EventState, StateMachine, StateStore
from app.modules.rule_engine.timeline import TemporalTracker


def test_temporal_active_ratio():
    tt = TemporalTracker([10, 30])
    for i in range(10):
        tt.record("R", 1, at(i), active=(i % 2 == 0))
    ratio = tt.active_ratio("R", 1, at(9), 30)
    assert 0.4 <= ratio <= 0.6


def test_temporal_summary_windows():
    tt = TemporalTracker([10, 30, 60])
    tt.record("R", 1, at(0), True)
    summary = tt.summary("R", 1, at(1))
    assert set(summary.keys()) == {"10s", "30s", "60s"}


def test_state_store_get_create():
    store = StateStore(max_states=10)
    s1 = store.get_or_create("R", 1, 1)
    s2 = store.get_or_create("R", 1, 1)
    assert s1 is s2
    assert store.count == 1


def test_state_store_capacity_evicts():
    store = StateStore(max_states=2)
    for tid in range(3):
        s = store.get_or_create("R", tid, 1)
        s.updated_ts = at(tid)
    assert store.count <= 2


def test_state_machine_transitions():
    assert StateMachine.can_transition(EventState.NEW, EventState.CONFIRMED)
    assert not StateMachine.can_transition(EventState.ENDED, EventState.ACTIVE)
    assert (
        StateMachine.transition(EventState.CONFIRMED, EventState.ENDED)
        == EventState.ENDED
    )
