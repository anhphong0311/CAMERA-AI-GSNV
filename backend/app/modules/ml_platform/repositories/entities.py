"""Domain entities — ML Platform (Sprint 13)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return str(uuid.uuid4())


@dataclass
class DatasetEntity:
    name: str
    description: str = ""
    source_type: str = "image"
    id: str = field(default_factory=_id)
    tags: List[str] = field(default_factory=list)
    item_count: int = 0
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "tags": self.tags,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DatasetVersionEntity:
    dataset_id: str
    version: str
    id: str = field(default_factory=_id)
    split_train: float = 0.8
    split_val: float = 0.1
    split_test: float = 0.1
    item_count: int = 0
    notes: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "version": self.version,
            "split_train": self.split_train,
            "split_val": self.split_val,
            "split_test": self.split_test,
            "item_count": self.item_count,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DatasetItemEntity:
    dataset_id: str
    path: str
    media_type: str = "image"
    id: str = field(default_factory=_id)
    version_id: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    annotated: bool = False
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "version_id": self.version_id,
            "path": self.path,
            "media_type": self.media_type,
            "labels": self.labels,
            "metadata": self.metadata,
            "annotated": self.annotated,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AnnotationEntity:
    item_id: str
    label: str
    id: str = field(default_factory=_id)
    tool: str = "internal"
    bbox: Optional[List[float]] = None
    polygon: Optional[List[List[float]]] = None
    confidence: Optional[float] = None
    annotator: Optional[str] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "label": self.label,
            "tool": self.tool,
            "bbox": self.bbox,
            "polygon": self.polygon,
            "confidence": self.confidence,
            "annotator": self.annotator,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TrainingJobEntity:
    name: str
    dataset_version_id: str
    architecture: str = "yolo11"
    id: str = field(default_factory=_id)
    status: str = "pending"
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    model_version_id: Optional[int] = None
    output_path: Optional[str] = None
    gpu_device: str = "cuda:0"
    progress: float = 0.0
    current_epoch: int = 0
    total_epochs: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "dataset_version_id": self.dataset_version_id,
            "architecture": self.architecture,
            "status": self.status,
            "config": self.config,
            "metrics": self.metrics,
            "model_version_id": self.model_version_id,
            "output_path": self.output_path,
            "gpu_device": self.gpu_device,
            "progress": round(self.progress, 2),
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TrainingEpochEntity:
    job_id: str
    epoch: int
    id: str = field(default_factory=_id)
    loss: float = 0.0
    val_loss: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    map50: float = 0.0
    map50_95: float = 0.0
    gpu_mem_mb: float = 0.0
    duration_s: float = 0.0
    recorded_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "epoch": self.epoch,
            "loss": round(self.loss, 4),
            "val_loss": round(self.val_loss, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "map50": round(self.map50, 4),
            "map50_95": round(self.map50_95, 4),
            "f1": round(
                2 * self.precision * self.recall / (self.precision + self.recall + 1e-9), 4
            ),
            "gpu_mem_mb": round(self.gpu_mem_mb, 1),
            "duration_s": round(self.duration_s, 2),
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class FpFnCaseEntity:
    case_type: str
    media_path: str
    prediction: Dict[str, Any]
    id: str = field(default_factory=_id)
    ground_truth: Optional[Dict[str, Any]] = None
    status: str = "open"
    event_id: Optional[str] = None
    camera_id: Optional[int] = None
    notes: str = ""
    marked_by: Optional[str] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "case_type": self.case_type,
            "media_path": self.media_path,
            "prediction": self.prediction,
            "ground_truth": self.ground_truth,
            "status": self.status,
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "notes": self.notes,
            "marked_by": self.marked_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ActiveLearningItemEntity:
    item_id: str
    reason: str
    id: str = field(default_factory=_id)
    confidence: float = 0.0
    status: str = "queued"
    dataset_id: Optional[str] = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "dataset_id": self.dataset_id,
            "reason": self.reason,
            "confidence": round(self.confidence, 4),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
