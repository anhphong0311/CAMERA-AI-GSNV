"""
Worker Pool (Sprint 10) — pool worker độc lập cho từng stage pipeline.

Mỗi worker chạy daemon thread, lấy task từ PriorityQueue, không block nhau.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.modules.performance.queue.priority_queue import PriorityQueue

TaskHandler = Callable[[Any], None]


@dataclass
class WorkerStats:
    name: str
    processed: int = 0
    errors: int = 0
    avg_latency_ms: float = 0.0
    alive: bool = False
    queue_depth: int = 0


class WorkerPool:
    """Generic worker pool với priority queue."""

    def __init__(
        self,
        name: str,
        num_workers: int,
        handler: TaskHandler,
        max_queue: int = 32,
    ) -> None:
        self.name = name
        self._num_workers = num_workers
        self._handler = handler
        self._queue: PriorityQueue[Any] = PriorityQueue(max_size=max_queue)
        self._threads: List[threading.Thread] = []
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._processed = 0
        self._errors = 0
        self._latency_sum = 0.0

    def start(self) -> None:
        with self._lock:
            if self._threads and any(t.is_alive() for t in self._threads):
                return
            self._stop.clear()
            self._threads = [
                threading.Thread(target=self._loop, name=f"{self.name}-{i}", daemon=True)
                for i in range(self._num_workers)
            ]
            for t in self._threads:
                t.start()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=timeout)
        self._threads = []

    def submit(self, task: Any, priority: int = 5) -> None:
        self._queue.put(task, priority=priority)

    def _loop(self) -> None:
        while not self._stop.is_set():
            task = self._queue.get()
            if task is None:
                time.sleep(0.005)
                continue
            start = time.perf_counter()
            try:
                self._handler(task)
                with self._lock:
                    self._processed += 1
                    self._latency_sum += (time.perf_counter() - start) * 1000
            except Exception:
                with self._lock:
                    self._errors += 1

    def stats(self) -> WorkerStats:
        with self._lock:
            avg = self._latency_sum / self._processed if self._processed else 0.0
            return WorkerStats(
                name=self.name,
                processed=self._processed,
                errors=self._errors,
                avg_latency_ms=round(avg, 2),
                alive=any(t.is_alive() for t in self._threads),
                queue_depth=self._queue.size,
            )


class WorkerPoolRegistry:
    """Registry nhiều pool — không global mutable state ngoài instance."""

    def __init__(self) -> None:
        self._pools: Dict[str, WorkerPool] = {}
        self._lock = threading.RLock()

    def register(self, pool: WorkerPool) -> None:
        with self._lock:
            self._pools[pool.name] = pool

    def get(self, name: str) -> Optional[WorkerPool]:
        with self._lock:
            return self._pools.get(name)

    def start_all(self) -> None:
        with self._lock:
            for p in self._pools.values():
                p.start()

    def stop_all(self) -> None:
        with self._lock:
            for p in self._pools.values():
                p.stop()

    def all_stats(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "name": s.name,
                    "processed": s.processed,
                    "errors": s.errors,
                    "avg_latency_ms": s.avg_latency_ms,
                    "alive": s.alive,
                    "queue_depth": s.queue_depth,
                }
                for p in self._pools.values()
                for s in [p.stats()]
            ]
