"""Unit test — Priority Queue."""

from __future__ import annotations

from app.modules.performance.queue.priority_queue import PriorityQueue


def test_priority_order():
    q: PriorityQueue[str] = PriorityQueue(max_size=10)
    q.put("low", priority=10)
    q.put("high", priority=1)
    assert q.get() == "high"
    assert q.get() == "low"


def test_drop_oldest_when_full():
    q: PriorityQueue[int] = PriorityQueue(max_size=2, drop_policy="oldest")
    q.put(1)
    q.put(2)
    q.put(3)
    assert q.dropped >= 1
    assert q.size <= 2


def test_stats():
    q: PriorityQueue[int] = PriorityQueue(max_size=5)
    q.put(1, priority=1)
    stats = q.stats()
    assert stats["size"] == 1
    assert stats["max_size"] == 5
