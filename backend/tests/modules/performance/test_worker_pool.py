"""Unit test — Worker Pool."""

from __future__ import annotations

import time

from app.modules.performance.pool.worker_pool import WorkerPool, WorkerPoolRegistry


def test_worker_pool_processes_tasks():
    processed = []

    def handler(task):
        processed.append(task)

    pool = WorkerPool("test", num_workers=2, handler=handler, max_queue=16)
    pool.start()
    for i in range(10):
        pool.submit(i)
    time.sleep(0.3)
    pool.stop()
    assert len(processed) >= 5
    stats = pool.stats()
    assert stats.processed >= 5
    assert stats.alive is False


def test_registry_all_stats():
    reg = WorkerPoolRegistry()
    pool = WorkerPool("a", 1, lambda x: None, max_queue=4)
    reg.register(pool)
    reg.start_all()
    pool.submit(1)
    time.sleep(0.1)
    reg.stop_all()
    assert len(reg.all_stats()) == 1
