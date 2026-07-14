"""Test EventProcessor state machine + pipeline."""

from __future__ import annotations

import pytest

from app.modules.event.event_processor import EventStateMachine
from app.modules.event.exceptions import InvalidEventError
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.status import EventStatus

from .conftest import build_service, frame, make_event


def test_state_machine_order_and_transitions():
    order = EventStateMachine.order()
    assert order[0] == EventStatus.NEW
    assert order[-1] == EventStatus.COMPLETED
    assert EventStateMachine.can_transition(EventStatus.NEW, EventStatus.VALIDATING)
    assert EventStateMachine.can_transition(EventStatus.PROCESSING, EventStatus.FAILED)
    assert not EventStateMachine.can_transition(
        EventStatus.COMPLETED, EventStatus.NEW
    )


def test_processor_creates_record_and_snapshot(tmp_path):
    service, _ = build_service(tmp_path, process_notification=False)
    service.push_frame(1, frame())
    ev = make_event()
    service.ingest(ev)
    records = service.process_events()
    assert len(records) == 1
    rec = records[0]
    assert rec.event_id == ev.event_id
    assert rec.snapshot is not None and rec.snapshot.status == "created"
    # process_notification=False → COMPLETED ngay
    assert rec.status == EventStatus.COMPLETED


def test_processor_invalid_event_raises(tmp_path):
    service, _ = build_service(tmp_path)
    bad = BehaviorEventInput(camera_id=1, track_id=1, rule_id="")
    with pytest.raises(InvalidEventError):
        service._processor.process(bad)
