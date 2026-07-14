"""
Pipeline Orchestrator (Sprint 10) — nối Camera → AI async qua FrameScheduler.

Không sửa CameraWorker/RuleEngine — chỉ đọc frame buffer và submit AI pipeline.
Downstream workers (tracking/behavior/rule/event) là optional chain qua WorkerPool.
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Callable, Dict, Optional

from loguru import logger

from app.modules.performance.config.loader import PipelineConfig
from app.modules.performance.pool.worker_pool import WorkerPool, WorkerPoolRegistry
from app.modules.performance.scheduler.frame_scheduler import FrameScheduler


class PipelineOrchestrator:
    """
    Async bridge: poll camera buffers → frame scheduler → AI submit.

    Chạy asyncio task, không block camera threads.
    """

    def __init__(
        self,
        frame_scheduler: FrameScheduler,
        config: PipelineConfig,
        *,
        get_camera_manager: Callable[[], Any],
        get_ai_service: Callable[[], Any],
        worker_registry: WorkerPoolRegistry,
    ) -> None:
        self._scheduler = frame_scheduler
        self._config = config
        self._get_camera_manager = get_camera_manager
        self._get_ai_service = get_ai_service
        self._workers = worker_registry
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._frame_counters: Dict[int, int] = {}
        self._lock = threading.Lock()
        self._submitted = 0
        self._polled = 0
        self._poll_offset = 0

    async def start(self) -> None:
        if self._running or not self._config.enabled:
            return
        self._running = True
        self._workers.start_all()
        self._task = asyncio.create_task(self._loop())
        logger.info("Pipeline orchestrator started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._workers.stop_all()
        logger.info("Pipeline orchestrator stopped")

    async def _loop(self) -> None:
        interval = self._config.poll_interval_ms / 1000.0
        while self._running:
            try:
                await asyncio.to_thread(self._poll_cameras)
            except Exception as exc:
                logger.warning("Pipeline poll error: {}", exc)
            await asyncio.sleep(interval)

    def _poll_cameras(self) -> None:
        manager = self._get_camera_manager()
        ai = self._get_ai_service()
        if manager is None or ai is None:
            return

        workers = getattr(manager, "_workers", {})
        camera_ids = sorted(workers.keys())
        if not camera_ids:
            return
        for i in range(len(camera_ids)):
            camera_id = camera_ids[(self._poll_offset + i) % len(camera_ids)]
            worker = workers.get(camera_id)
            if worker is None or not getattr(worker, "is_running", False):
                continue
            frame_buf = getattr(worker, "frame_buffer", None)
            if frame_buf is None:
                continue
            packet = frame_buf.latest()
            if packet is None:
                continue
            self._polled += 1
            cnt = self._frame_counters.get(camera_id, 0) + 1
            self._frame_counters[camera_id] = cnt
            if not self._scheduler.should_process(camera_id):
                continue
            ai.submit_frame(camera_id, packet.data, cnt)
            self._submitted += 1
        self._poll_offset = (self._poll_offset + 1) % len(camera_ids)

    def stats(self) -> dict:
        return {
            "enabled": self._config.enabled,
            "polled": self._polled,
            "submitted": self._submitted,
            "frame_scheduler": self._scheduler.summary(),
            "workers": self._workers.all_stats(),
        }
