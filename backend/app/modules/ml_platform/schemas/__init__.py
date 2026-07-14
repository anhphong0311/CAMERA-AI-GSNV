"""Pydantic schemas — ML Platform API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetCreateBody(BaseModel):
    name: str
    description: str = ""
    source_type: str = "image"
    tags: List[str] = Field(default_factory=list)


class DatasetImportBody(BaseModel):
    paths: List[str]
    media_type: str = "image"
    version_id: Optional[str] = None


class DatasetVersionBody(BaseModel):
    version: str
    split_train: float = 0.8
    split_val: float = 0.1
    split_test: float = 0.1
    notes: str = ""


class DatasetMergeBody(BaseModel):
    source_ids: List[str]
    target_name: str


class AnnotationCreateBody(BaseModel):
    item_id: str
    label: str
    bbox: Optional[List[float]] = None
    polygon: Optional[List[List[float]]] = None
    tool: str = "internal"


class ExternalToolConfigBody(BaseModel):
    tool: str
    config: Dict[str, Any] = Field(default_factory=dict)


class TrainingJobCreateBody(BaseModel):
    name: str
    dataset_version_id: str
    architecture: str = "yolo11"
    config: Optional[Dict[str, Any]] = None


class DeployBody(BaseModel):
    model_id: int


class RollbackBody(BaseModel):
    name: str


class AbTestBody(BaseModel):
    name: str
    model_a_id: int
    model_b_id: int
    traffic_b_pct: float = 10.0


class BenchmarkBody(BaseModel):
    model_path: Optional[str] = None
    architecture: str = "yolo11"
    runs: int = Field(default=50, ge=5, le=200)


class FpFnCreateBody(BaseModel):
    case_type: str
    media_path: str
    prediction: Dict[str, Any]
    ground_truth: Optional[Dict[str, Any]] = None
    event_id: Optional[str] = None
    camera_id: Optional[int] = None


class ActiveLearningBody(BaseModel):
    item_id: str
    confidence: float
    reason: str = "low_confidence"
    dataset_id: Optional[str] = None
