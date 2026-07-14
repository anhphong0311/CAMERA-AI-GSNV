"""Training Manager Service."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

from app.exceptions.base import ConflictError, NotFoundError
from app.modules.ml_platform.config.labels import DEFAULT_TRAIN_CONFIG, SUPPORTED_ARCHITECTURES
from app.modules.ml_platform.repositories.base import (
    DatasetVersionRepository,
    TrainingEpochRepository,
    TrainingJobRepository,
)
from app.modules.ml_platform.repositories.entities import TrainingEpochEntity, TrainingJobEntity
from app.modules.ml_platform.training.augment import merge_augmentation
from app.modules.ml_platform.training.runner import run_training_job


class TrainingService:
    """Quản lý training jobs — start, resume, cancel, history."""

    def __init__(
        self,
        jobs: TrainingJobRepository,
        epochs: TrainingEpochRepository,
        versions: DatasetVersionRepository,
    ) -> None:
        self._jobs = jobs
        self._epochs = epochs
        self._versions = versions
        self._tasks: Dict[str, asyncio.Task] = {}
        self._on_complete_callbacks: List[Any] = []

    def register_on_complete(self, callback) -> None:
        self._on_complete_callbacks.append(callback)

    def list_jobs(self) -> List[TrainingJobEntity]:
        return sorted(self._jobs.list(), key=lambda j: j.created_at, reverse=True)

    def get_job(self, job_id: str) -> TrainingJobEntity:
        job = self._jobs.get(job_id)
        if job is None:
            raise NotFoundError("TrainingJob", job_id)
        return job

    def create_job(
        self,
        name: str,
        dataset_version_id: str,
        *,
        architecture: str = "yolo11",
        config: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> TrainingJobEntity:
        if architecture not in SUPPORTED_ARCHITECTURES:
            raise ValueError(f"Architecture không hỗ trợ: {architecture}")
        ver = self._versions.get(dataset_version_id)
        if ver is None:
            raise NotFoundError("DatasetVersion", dataset_version_id)
        merged = {**DEFAULT_TRAIN_CONFIG, **(config or {})}
        merged["augmentation"] = merge_augmentation(merged.get("augmentation"))
        entity = TrainingJobEntity(
            name=name,
            dataset_version_id=dataset_version_id,
            architecture=architecture,
            config=merged,
            total_epochs=int(merged.get("epochs", 100)),
            created_by=created_by,
        )
        return self._jobs.save(entity)

    async def start_job(self, job_id: str, *, simulate: bool = True) -> TrainingJobEntity:
        job = self.get_job(job_id)
        if job.status == "running":
            raise ConflictError("Job đang chạy.")
        if job.status == "completed":
            raise ConflictError("Job đã hoàn thành — tạo job mới.")

        def on_epoch(ep: TrainingEpochEntity) -> None:
            self._epochs.save(ep)
            job.current_epoch = ep.epoch
            job.progress = round(ep.epoch / max(job.total_epochs, 1) * 100, 2)
            self._jobs.save(job)

        def on_complete(j: TrainingJobEntity, metrics: Dict[str, Any]) -> None:
            j.metrics = metrics
            self._jobs.save(j)
            for cb in self._on_complete_callbacks:
                try:
                    cb(j)
                except Exception as exc:
                    logger.warning("Training complete callback lỗi: {}", exc)

        task = asyncio.create_task(
            run_training_job(job, on_epoch=on_epoch, on_complete=on_complete, simulate=simulate)
        )
        self._tasks[job_id] = task
        job.status = "running"
        return self._jobs.save(job)

    def cancel_job(self, job_id: str) -> TrainingJobEntity:
        job = self.get_job(job_id)
        task = self._tasks.pop(job_id, None)
        if task and not task.done():
            task.cancel()
        job.status = "cancelled"
        return self._jobs.save(job)

    def epoch_history(self, job_id: str) -> List[TrainingEpochEntity]:
        self.get_job(job_id)
        return self._epochs.list(job_id)

    def training_history_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": j.id,
                "name": j.name,
                "status": j.status,
                "architecture": j.architecture,
                "epochs": j.current_epoch,
                "metrics": j.metrics,
            }
            for j in self.list_jobs()
        ]
