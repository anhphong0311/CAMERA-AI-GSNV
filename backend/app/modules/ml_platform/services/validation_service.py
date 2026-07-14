"""Validation & Evaluation Services."""

from __future__ import annotations

from typing import Any, Dict, List

from app.modules.ml_platform.repositories.entities import TrainingEpochEntity, TrainingJobEntity


class ValidationService:
    """Tính metrics validation từ epoch history."""

    def metrics_from_epochs(self, epochs: List[TrainingEpochEntity]) -> Dict[str, Any]:
        if not epochs:
            return {}
        last = epochs[-1]
        f1 = 2 * last.precision * last.recall / (last.precision + last.recall + 1e-9)
        return {
            "precision": last.precision,
            "recall": last.recall,
            "f1": round(f1, 4),
            "map50": last.map50,
            "map50_95": last.map50_95,
            "loss": last.loss,
            "val_loss": last.val_loss,
        }

    def loss_curve(self, epochs: List[TrainingEpochEntity]) -> List[Dict[str, float]]:
        return [{"epoch": e.epoch, "loss": e.loss, "val_loss": e.val_loss} for e in epochs]

    def accuracy_curve(self, epochs: List[TrainingEpochEntity]) -> List[Dict[str, float]]:
        return [{"epoch": e.epoch, "map50": e.map50, "map50_95": e.map50_95} for e in epochs]


class EvaluationService:
    """Đánh giá model sau training."""

    def evaluate_job(self, job: TrainingJobEntity, epochs: List[TrainingEpochEntity]) -> Dict[str, Any]:
        validator = ValidationService()
        metrics = validator.metrics_from_epochs(epochs)
        return {
            "job_id": job.id,
            "architecture": job.architecture,
            "status": job.status,
            "metrics": metrics,
            "confusion_matrix": job.metrics.get("confusion_matrix"),
            "loss_curve": validator.loss_curve(epochs),
            "accuracy_curve": validator.accuracy_curve(epochs),
            "passed": metrics.get("map50", 0) >= 0.5,
        }

    def compare_jobs(self, jobs: List[TrainingJobEntity]) -> List[Dict[str, Any]]:
        return sorted(
            [
                {
                    "job_id": j.id,
                    "name": j.name,
                    "map50": j.metrics.get("map50", 0),
                    "map50_95": j.metrics.get("map50_95", 0),
                    "f1": j.metrics.get("f1", 0),
                }
                for j in jobs
                if j.status == "completed"
            ],
            key=lambda x: x["map50_95"],
            reverse=True,
        )
