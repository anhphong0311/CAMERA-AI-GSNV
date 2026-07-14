"""
Training runner — pipeline huấn luyện (Sprint 13).

Mô phỏng vòng train/validate khi không có GPU (CI/test).
Production: gọi Ultralytics YOLO train API khi weights + CUDA khả dụng.
"""

from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from loguru import logger

from app.modules.ml_platform.config.labels import DEFAULT_TRAIN_CONFIG
from app.modules.ml_platform.repositories.entities import TrainingEpochEntity, TrainingJobEntity


async def run_training_job(
    job: TrainingJobEntity,
    *,
    on_epoch: Callable[[TrainingEpochEntity], None],
    on_complete: Callable[[TrainingJobEntity, Dict[str, Any]], None],
    simulate: bool = True,
) -> None:
    """
    Chạy training job (async).

    Args:
        job: TrainingJobEntity đã persist.
        on_epoch: callback mỗi epoch.
        on_complete: callback khi hoàn thành (metrics cuối).
        simulate: True = mô phỏng (CI); False = gọi YOLO thật nếu có.
    """
    cfg = {**DEFAULT_TRAIN_CONFIG, **(job.config or {})}
    epochs = int(cfg.get("epochs", 10))
    job.total_epochs = epochs
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)

    if simulate or not _can_train_real():
        await _simulate_training(job, epochs, cfg, on_epoch, on_complete)
    else:
        await _real_training(job, epochs, cfg, on_epoch, on_complete)


def _can_train_real() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


async def _simulate_training(
    job: TrainingJobEntity,
    epochs: int,
    cfg: Dict[str, Any],
    on_epoch: Callable[[TrainingEpochEntity], None],
    on_complete: Callable[[TrainingJobEntity, Dict[str, Any]], None],
) -> None:
    """Mô phỏng loss/mAP giảm dần theo epoch."""
    base_loss = 2.5
    for ep in range(1, epochs + 1):
        await asyncio.sleep(0.05)
        decay = math.exp(-ep / max(epochs, 1) * 2)
        loss = base_loss * decay + random.uniform(0, 0.05)
        val_loss = loss * 1.1
        precision = min(0.99, 0.5 + ep / epochs * 0.45 + random.uniform(-0.02, 0.02))
        recall = min(0.99, 0.48 + ep / epochs * 0.42 + random.uniform(-0.02, 0.02))
        map50 = min(0.99, 0.45 + ep / epochs * 0.5)
        map50_95 = map50 * 0.75

        epoch_entity = TrainingEpochEntity(
            job_id=job.id,
            epoch=ep,
            loss=loss,
            val_loss=val_loss,
            precision=precision,
            recall=recall,
            map50=map50,
            map50_95=map50_95,
            gpu_mem_mb=random.uniform(2048, 8192) if cfg.get("device", "").startswith("cuda") else 0,
            duration_s=random.uniform(30, 120),
        )
        job.current_epoch = ep
        job.progress = round(ep / epochs * 100, 2)
        on_epoch(epoch_entity)

    final_metrics = {
        "precision": epoch_entity.precision,
        "recall": epoch_entity.recall,
        "f1": round(
            2 * epoch_entity.precision * epoch_entity.recall
            / (epoch_entity.precision + epoch_entity.recall + 1e-9),
            4,
        ),
        "map50": epoch_entity.map50,
        "map50_95": epoch_entity.map50_95,
        "loss": epoch_entity.loss,
        "confusion_matrix": _mock_confusion_matrix(),
    }
    job.metrics = final_metrics
    job.status = "completed"
    job.finished_at = datetime.now(timezone.utc)
    job.progress = 100.0
    job.output_path = str(Path("models") / f"{job.name}_{job.id[:8]}.pt")
    on_complete(job, final_metrics)
    logger.info("Training job {} completed (simulated)", job.id)


async def _real_training(
    job: TrainingJobEntity,
    epochs: int,
    cfg: Dict[str, Any],
    on_epoch: Callable[[TrainingEpochEntity], None],
    on_complete: Callable[[TrainingJobEntity, Dict[str, Any]], None],
) -> None:
    """Huấn luyện YOLO thật qua Ultralytics (khi có GPU)."""
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.warning("Ultralytics không có — fallback simulate")
        await _simulate_training(job, epochs, cfg, on_epoch, on_complete)
        return

    model_name = _arch_to_weights(job.architecture)
    model = YOLO(model_name)
    results = model.train(
        data=cfg.get("data_yaml", "config/dataset.yaml"),
        epochs=epochs,
        batch=int(cfg.get("batch_size", 16)),
        imgsz=int(cfg.get("image_size", 640)),
        lr0=float(cfg.get("learning_rate", 0.001)),
        device=cfg.get("device", "0"),
        amp=bool(cfg.get("mixed_precision", True)),
        resume=bool(cfg.get("resume", False)),
        project=str(Path("models/training")),
        name=job.name,
    )
    metrics = {
        "map50": float(getattr(results, "results_dict", {}).get("metrics/mAP50(B)", 0)),
        "map50_95": float(getattr(results, "results_dict", {}).get("metrics/mAP50-95(B)", 0)),
    }
    job.metrics = metrics
    job.status = "completed"
    job.finished_at = datetime.now(timezone.utc)
    job.output_path = str(Path("models/training") / job.name / "weights" / "best.pt")
    on_complete(job, metrics)


def _arch_to_weights(architecture: str) -> str:
    mapping = {
        "yolo11": "yolo11n.pt",
        "yolo12": "yolo11n.pt",
        "rt-detr": "rtdetr-l.pt",
        "custom": "yolo11n.pt",
    }
    return mapping.get(architecture, "yolo11n.pt")


def _mock_confusion_matrix() -> Dict[str, Any]:
    labels = ["person", "phone", "cup"]
    matrix = [[random.randint(80, 100) for _ in labels] for _ in labels]
    return {"labels": labels, "matrix": matrix}
