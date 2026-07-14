"""Test EventService facade + queries + store + integration pipeline."""

from __future__ import annotations

import numpy as np

from app.modules.event.repositories.store import InMemoryEventStore
from app.modules.event.schemas.records import EventRecord
from app.modules.event.schemas.status import EventStatus

from .conftest import at, build_service, frame, make_event


def test_service_queries(tmp_path):
    service, _ = build_service(tmp_path)
    service.push_frame(1, frame())
    service.ingest_now(make_event(event_id="e1"))
    service.ingest_now(make_event(event_id="e2", track_id=99, rule_id="EATING"))
    service.drain_notifications()

    assert service.get_event("e1").event_id == "e1"
    assert len(service.list_events()) == 2
    assert len(service.list_events(rule_id="EATING")) == 1
    stats = service.statistics()
    assert stats["store"]["total_events"] == 2
    assert stats["processed"] == 2


def test_service_ingest_dict_adapter(tmp_path):
    service, provider = build_service(tmp_path)
    # giả lập BehaviorEventDTO.to_dict() từ Rule Engine
    dto = {
        "event_id": "rule-1",
        "camera_id": 2,
        "track_id": 7,
        "rule_id": "SLEEPING",
        "event_type": "SLEEPING",
        "severity": "MEDIUM",
        "confidence": 0.8,
        "duration": 30.0,
        "start_time": at(0).isoformat(),
    }
    service.push_frame(2, frame())
    service.ingest_dict(dto)
    service.run_once()
    rec = service.get_event("rule-1")
    assert rec.rule_id == "SLEEPING"
    assert rec.camera_id == 2
    assert len(provider.sent) == 1


def test_inmemory_store_history_bound():
    store = InMemoryEventStore(history_size=3)
    for i in range(5):
        store.save(
            EventRecord(
                event_id=f"e{i}",
                camera_id=1,
                track_id=1,
                rule_id="R",
                event_type="R",
                severity="LOW",
                confidence=0.1,
                start_time=at(i),
                status=EventStatus.NEW,
            )
        )
    assert store.statistics()["total_events"] == 5
    assert store.statistics()["stored"] <= 3


def test_full_pipeline_integration(tmp_path):
    """Rule Engine event → Processor → Snapshot → Video → Notification → Telegram."""
    service, provider = build_service(tmp_path)
    # nạp frame trải 20s để có cả pre + post evidence
    for i in range(200):
        service.push_frame(1, frame(value=i % 255).astype(np.uint8), timestamp=at(i * 0.1))

    ev = make_event(start_time=at(10))
    service.ingest(ev)
    records = service.process_events()
    assert len(records) == 1
    rec = records[0]

    # snapshot tạo thành công
    assert rec.snapshot is not None and rec.snapshot.status == "created"
    # video evidence (created hoặc skipped tùy codec môi trường)
    assert rec.video is not None

    # notification queue hoạt động → drain gửi Telegram (memory provider)
    assert service._notification_queue.size >= 1
    service.drain_notifications()
    assert len(provider.sent) == 1
    assert rec.status == EventStatus.COMPLETED

    # notification/retry history
    assert len(service.notifications()) == 1
    assert service.telegram_status()["notification_queue"] == 0
