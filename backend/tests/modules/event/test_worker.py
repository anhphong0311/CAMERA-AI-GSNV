"""Test NotificationWorker: gửi, dedup/cooldown, retry, provider not ready."""

from __future__ import annotations

from app.modules.event.schemas.status import EventStatus, NotificationStatus

from .conftest import build_service, frame, make_event


def _process(service, event):
    service.push_frame(event.camera_id, frame())
    service.ingest(event)
    return service.process_events()[0]


def test_worker_sends_and_completes(tmp_path):
    service, provider = build_service(tmp_path)
    rec = _process(service, make_event())
    service.drain_notifications()
    assert rec.status == EventStatus.COMPLETED
    assert len(provider.sent) == 1
    assert rec.notifications[-1].status == NotificationStatus.SENT


def test_worker_dedup_blocks_second(tmp_path):
    service, provider = build_service(tmp_path)
    _process(service, make_event(event_id="a"))
    service.drain_notifications()
    _process(service, make_event(event_id="b"))  # cùng rule+track
    service.drain_notifications()
    # chỉ gửi 1 lần (lần 2 bị dedup/cooldown)
    assert len(provider.sent) == 1


def test_worker_retry_then_success(tmp_path):
    service, provider = build_service(tmp_path, fail_times=2)
    rec = _process(service, make_event())
    service.drain_notifications()
    assert len(provider.sent) == 1
    notif = rec.notifications[-1]
    assert notif.status == NotificationStatus.SENT
    assert notif.attempts == 3
    assert len(notif.retries) == 2


def test_worker_all_retries_fail(tmp_path):
    service, provider = build_service(tmp_path, fail_times=99)
    rec = _process(service, make_event())
    service.drain_notifications()
    assert len(provider.sent) == 0
    assert rec.status == EventStatus.FAILED
    assert rec.notifications[-1].status == NotificationStatus.FAILED


def test_worker_provider_not_ready_skips(tmp_path):
    service, provider = build_service(tmp_path, ready=False)
    rec = _process(service, make_event())
    service.drain_notifications()
    assert len(provider.sent) == 0
    assert rec.status == EventStatus.COMPLETED
    assert rec.notifications[-1].status == NotificationStatus.SKIPPED


def test_resend_force_bypasses_dedup(tmp_path):
    service, provider = build_service(tmp_path)
    ev = make_event()
    _process(service, ev)
    service.drain_notifications()
    assert len(provider.sent) == 1
    service.resend(ev.event_id, force=True)
    assert len(provider.sent) == 2
