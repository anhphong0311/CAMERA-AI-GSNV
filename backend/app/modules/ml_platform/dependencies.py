"""Dependency injection — ML Platform (Sprint 13)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, Request
from loguru import logger

from app.modules.ml_platform.repositories.memory import (
    InMemoryActiveLearningRepository,
    InMemoryAnnotationRepository,
    InMemoryDatasetItemRepository,
    InMemoryDatasetRepository,
    InMemoryDatasetVersionRepository,
    InMemoryFpFnRepository,
    InMemoryTrainingEpochRepository,
    InMemoryTrainingJobRepository,
)
from app.modules.ml_platform.services.annotation_service import AnnotationService
from app.modules.ml_platform.services.dataset_service import DatasetService
from app.modules.ml_platform.services.fp_fn_service import ActiveLearningService, FpFnService
from app.modules.ml_platform.services.registry_service import (
    BenchmarkService,
    DeploymentService,
    RegistryService,
)
from app.modules.ml_platform.services.training_service import TrainingService
from app.modules.ml_platform.services.validation_service import EvaluationService, ValidationService


@dataclass
class MLPlatformContainer:
    """Gói services ML Platform."""

    datasets: DatasetService
    annotations: AnnotationService
    training: TrainingService
    validation: ValidationService
    evaluation: EvaluationService
    registry: RegistryService
    deployment: DeploymentService
    benchmark: BenchmarkService
    fp_fn: FpFnService
    active_learning: ActiveLearningService


def _build_container(admin_models=None) -> MLPlatformContainer:
    ds_repo = InMemoryDatasetRepository()
    ver_repo = InMemoryDatasetVersionRepository()
    item_repo = InMemoryDatasetItemRepository()
    ann_repo = InMemoryAnnotationRepository()
    job_repo = InMemoryTrainingJobRepository()
    epoch_repo = InMemoryTrainingEpochRepository()
    fpfn_repo = InMemoryFpFnRepository()
    al_repo = InMemoryActiveLearningRepository()

    datasets = DatasetService(ds_repo, ver_repo, item_repo)
    annotations = AnnotationService(ann_repo, item_repo)
    training = TrainingService(job_repo, epoch_repo, ver_repo)
    registry = RegistryService(admin_models)
    deployment = DeploymentService(admin_models)

    def on_train_complete(job):
        registry.register_from_training(job, uploaded_by=job.created_by)

    training.register_on_complete(on_train_complete)

    return MLPlatformContainer(
        datasets=datasets,
        annotations=annotations,
        training=training,
        validation=ValidationService(),
        evaluation=EvaluationService(),
        registry=registry,
        deployment=deployment,
        benchmark=BenchmarkService(),
        fp_fn=FpFnService(fpfn_repo, item_repo),
        active_learning=ActiveLearningService(al_repo, item_repo),
    )


async def init_ml_platform_module(app: FastAPI) -> None:
    admin = getattr(app.state, "admin", None)
    admin_models = admin.models if admin else None
    container = _build_container(admin_models)
    app.state.ml_platform = container
    logger.info("ML Platform module initialized (v2.0 Sprint 13)")


async def shutdown_ml_platform_module(app: FastAPI) -> None:
    app.state.ml_platform = None
    logger.info("ML Platform module shutdown")


def get_ml_platform(request: Request) -> MLPlatformContainer:
    container: Optional[MLPlatformContainer] = getattr(request.app.state, "ml_platform", None)
    if container is None:
        raise RuntimeError("ML Platform module chưa khởi tạo")
    return container
