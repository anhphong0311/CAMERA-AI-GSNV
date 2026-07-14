"""Test dedup/cooldown + retry policy + queue."""

from __future__ import annotations

from datetime import timedelta

from app.modules.event.config import RetryConfig
from app.modules.event.notification.dedup import DedupCooldown
from app.modules.event.notification.provider import SendResult
from app.modules.event.queue.queues import BoundedQueue
from app.modules.event.retry.policy import RetryPolicy

from .conftest import BASE_TIME


def test_dedup_blocks_same_rule_person_within_window():
    dc = DedupCooldown(dedup_window=300, cooldown_seconds=300)
    assert dc.should_send("PHONE", 1, BASE_TIME)
    dc.mark_sent("PHONE", 1, BASE_TIME)
    # trong 5 phút → chặn
    assert not dc.should_send("PHONE", 1, BASE_TIME + timedelta(seconds=60))
    # khác track → cho phép
    assert dc.should_send("PHONE", 2, BASE_TIME + timedelta(seconds=60))
    # sau cooldown → cho phép lại
    assert dc.should_send("PHONE", 1, BASE_TIME + timedelta(seconds=301))


def test_cooldown_cleanup():
    dc = DedupCooldown(dedup_window=10, cooldown_seconds=10)
    dc.mark_sent("R", 1, BASE_TIME)
    removed = dc.cleanup(BASE_TIME + timedelta(seconds=100))
    assert removed == 1


def test_retry_succeeds_after_failures():
    rc = RetryConfig(max_attempts=3, backoff=[0, 0, 0])
    policy = RetryPolicy(rc, sleeper=lambda s: None)
    calls = {"n": 0}

    def task():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("boom")
        return SendResult(ok=True)

    retries = []
    outcome = policy.run(task, on_retry=lambda a, d, e: retries.append((a, d, e)))
    assert outcome.ok
    assert outcome.attempts == 3
    assert len(retries) == 2


def test_retry_gives_up():
    rc = RetryConfig(max_attempts=3, backoff=[0, 0, 0])
    policy = RetryPolicy(rc, sleeper=lambda s: None)
    outcome = policy.run(lambda: (_ for _ in ()).throw(RuntimeError("x")))
    assert not outcome.ok
    assert outcome.attempts == 3


def test_retry_skipped_no_retry():
    rc = RetryConfig(max_attempts=3, backoff=[0, 0, 0])
    policy = RetryPolicy(rc, sleeper=lambda s: None)
    outcome = policy.run(lambda: SendResult(ok=False, skipped=True))
    assert outcome.skipped
    assert outcome.attempts == 1


def test_bounded_queue_fifo_and_drain():
    q: BoundedQueue[int] = BoundedQueue(max_size=10)
    for i in range(5):
        q.put(i)
    assert q.size == 5
    assert q.get() == 0
    rest = q.drain()
    assert rest == [1, 2, 3, 4]
    assert q.size == 0
    assert q.total_enqueued == 5
