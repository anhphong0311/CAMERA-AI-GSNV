"""
ML Platform API (Sprint 13 / v2.0).

Prefixes: /dataset, /annotation, /training, /model, /benchmark, /deployment
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.modules.admin.dependencies import get_current_user, require_permission
from app.modules.ml_platform.dependencies import MLPlatformContainer, get_ml_platform
from app.modules.ml_platform.schemas import (
    AbTestBody,
    ActiveLearningBody,
    AnnotationCreateBody,
    BenchmarkBody,
    DatasetCreateBody,
    DatasetImportBody,
    DatasetMergeBody,
    DatasetVersionBody,
    DeployBody,
    ExternalToolConfigBody,
    FpFnCreateBody,
    RollbackBody,
    TrainingJobCreateBody,
)
from app.schemas.common import ApiResponse

dataset_router = APIRouter(prefix="/dataset", tags=["ML Platform — Dataset"])
annotation_router = APIRouter(prefix="/annotation", tags=["ML Platform — Annotation"])
training_router = APIRouter(prefix="/training", tags=["ML Platform — Training"])
model_router = APIRouter(prefix="/model", tags=["ML Platform — Model Registry"])
benchmark_router = APIRouter(prefix="/benchmark", tags=["ML Platform — Benchmark"])
deployment_router = APIRouter(prefix="/deployment", tags=["ML Platform — Deployment"])

ML_PLATFORM_ROUTERS = [
    dataset_router,
    annotation_router,
    training_router,
    model_router,
    benchmark_router,
    deployment_router,
]


# ----- Dataset -----
@dataset_router.get("", response_model=ApiResponse[list])
async def list_datasets(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    tag: Optional[str] = None,
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[d.to_dict() for d in ml.datasets.list_datasets(tag=tag)])


@dataset_router.get("/statistics", response_model=ApiResponse[dict])
async def dataset_statistics(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.datasets.statistics())


@dataset_router.post("", response_model=ApiResponse[dict])
async def create_dataset(
    body: DatasetCreateBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:create")),
) -> ApiResponse[dict]:
    ds = ml.datasets.create_dataset(
        body.name, description=body.description, source_type=body.source_type, tags=body.tags
    )
    return ApiResponse(data=ds.to_dict())


@dataset_router.get("/{dataset_id}", response_model=ApiResponse[dict])
async def get_dataset(
    dataset_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.datasets.get_dataset(dataset_id).to_dict())


@dataset_router.delete("/{dataset_id}", response_model=ApiResponse[dict])
async def delete_dataset(
    dataset_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:delete")),
) -> ApiResponse[dict]:
    ml.datasets.delete_dataset(dataset_id)
    return ApiResponse(data={"deleted": dataset_id})


@dataset_router.post("/{dataset_id}/import", response_model=ApiResponse[list])
async def import_items(
    dataset_id: str,
    body: DatasetImportBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:create")),
) -> ApiResponse[list]:
    items = ml.datasets.import_items(
        dataset_id, body.paths, media_type=body.media_type, version_id=body.version_id
    )
    return ApiResponse(data=[i.to_dict() for i in items])


@dataset_router.get("/{dataset_id}/items", response_model=ApiResponse[list])
async def search_items(
    dataset_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    annotated: Optional[bool] = None,
    label: Optional[str] = None,
    q: Optional[str] = None,
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[list]:
    items = ml.datasets.search_items(dataset_id, annotated=annotated, label=label, q=q)
    return ApiResponse(data=[i.to_dict() for i in items])


@dataset_router.post("/{dataset_id}/versions", response_model=ApiResponse[dict])
async def create_version(
    dataset_id: str,
    body: DatasetVersionBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:create")),
) -> ApiResponse[dict]:
    ver = ml.datasets.create_version(
        dataset_id,
        body.version,
        split_train=body.split_train,
        split_val=body.split_val,
        split_test=body.split_test,
        notes=body.notes,
    )
    return ApiResponse(data=ver.to_dict())


@dataset_router.get("/{dataset_id}/versions", response_model=ApiResponse[list])
async def list_versions(
    dataset_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[v.to_dict() for v in ml.datasets.list_versions(dataset_id)])


@dataset_router.post("/{dataset_id}/versions/{version_id}/split", response_model=ApiResponse[dict])
async def split_dataset(
    dataset_id: str,
    version_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.datasets.split_dataset(dataset_id, version_id))


@dataset_router.post("/merge", response_model=ApiResponse[dict])
async def merge_datasets(
    body: DatasetMergeBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:create")),
) -> ApiResponse[dict]:
    ds = ml.datasets.merge_datasets(body.source_ids, body.target_name)
    return ApiResponse(data=ds.to_dict())


@dataset_router.get("/{dataset_id}/export", response_model=ApiResponse[dict])
async def export_dataset(
    dataset_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.datasets.export_manifest(dataset_id))


# ----- Annotation -----
@annotation_router.get("/labels", response_model=ApiResponse[list])
async def list_labels(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("annotation:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=ml.annotations.label_classes())


@annotation_router.get("/tools", response_model=ApiResponse[list])
async def list_tools(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("annotation:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=ml.annotations.supported_tools())


@annotation_router.post("/configure", response_model=ApiResponse[dict])
async def configure_tool(
    body: ExternalToolConfigBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("annotation:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.annotations.configure_external(body.tool, body.config))


@annotation_router.get("/external-status", response_model=ApiResponse[dict])
async def external_status(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("annotation:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.annotations.external_status())


@annotation_router.post("", response_model=ApiResponse[dict])
async def create_annotation(
    body: AnnotationCreateBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("annotation:create")),
) -> ApiResponse[dict]:
    ann = ml.annotations.create_annotation(
        body.item_id,
        body.label,
        bbox=body.bbox,
        polygon=body.polygon,
        tool=body.tool,
        annotator=user.get("username"),
    )
    return ApiResponse(data=ann.to_dict())


@annotation_router.get("", response_model=ApiResponse[list])
async def list_annotations(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    item_id: Optional[str] = None,
    _: dict = Depends(require_permission("annotation:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[a.to_dict() for a in ml.annotations.list_annotations(item_id)])


# ----- Training -----
@training_router.get("", response_model=ApiResponse[list])
async def list_training_jobs(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[j.to_dict() for j in ml.training.list_jobs()])


@training_router.get("/history", response_model=ApiResponse[list])
async def training_history(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=ml.training.training_history_summary())


@training_router.post("", response_model=ApiResponse[dict])
async def create_training_job(
    body: TrainingJobCreateBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("training:create")),
) -> ApiResponse[dict]:
    job = ml.training.create_job(
        body.name,
        body.dataset_version_id,
        architecture=body.architecture,
        config=body.config,
        created_by=user.get("username"),
    )
    return ApiResponse(data=job.to_dict())


@training_router.get("/{job_id}", response_model=ApiResponse[dict])
async def get_training_job(
    job_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.training.get_job(job_id).to_dict())


@training_router.post("/{job_id}/start", response_model=ApiResponse[dict])
async def start_training(
    job_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    simulate: bool = Query(default=True),
    _: dict = Depends(require_permission("training:update")),
) -> ApiResponse[dict]:
    job = await ml.training.start_job(job_id, simulate=simulate)
    return ApiResponse(data=job.to_dict())


@training_router.post("/{job_id}/cancel", response_model=ApiResponse[dict])
async def cancel_training(
    job_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.training.cancel_job(job_id).to_dict())


@training_router.get("/{job_id}/epochs", response_model=ApiResponse[list])
async def training_epochs(
    job_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[list]:
    epochs = ml.training.epoch_history(job_id)
    return ApiResponse(data=[e.to_dict() for e in epochs])


@training_router.get("/{job_id}/evaluate", response_model=ApiResponse[dict])
async def evaluate_training(
    job_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[dict]:
    job = ml.training.get_job(job_id)
    epochs = ml.training.epoch_history(job_id)
    return ApiResponse(data=ml.evaluation.evaluate_job(job, epochs))


@training_router.get("/compare/completed", response_model=ApiResponse[list])
async def compare_training_jobs(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[list]:
    completed = [j for j in ml.training.list_jobs() if j.status == "completed"]
    return ApiResponse(data=ml.evaluation.compare_jobs(completed))


# ----- Model Registry -----
@model_router.get("", response_model=ApiResponse[list])
async def list_models(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("models:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=ml.registry.list_entries())


# ----- Benchmark -----
@benchmark_router.post("/run", response_model=ApiResponse[dict])
async def run_benchmark(
    body: BenchmarkBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.benchmark.benchmark(
        model_path=body.model_path, architecture=body.architecture, runs=body.runs
    ))


# ----- Deployment -----
@deployment_router.post("/deploy", response_model=ApiResponse[dict])
async def deploy_model(
    body: DeployBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.deployment.deploy(body.model_id, actor=user.get("username")))


@deployment_router.post("/rollback", response_model=ApiResponse[dict])
async def rollback_model(
    body: RollbackBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.deployment.rollback(body.name, actor=user.get("username")))


@deployment_router.post("/ab-test", response_model=ApiResponse[dict])
async def start_ab_test(
    body: AbTestBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("models:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.deployment.start_ab_test(
        body.name, body.model_a_id, body.model_b_id, body.traffic_b_pct
    ))


@deployment_router.get("/ab-test", response_model=ApiResponse[dict])
async def ab_test_status(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("models:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.deployment.ab_status())


# ----- FP/FN & Active Learning (under dataset router extras) -----
@dataset_router.get("/fp-fn/cases", response_model=ApiResponse[list])
async def list_fp_fn(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    case_type: Optional[str] = None,
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[c.to_dict() for c in ml.fp_fn.list_cases(case_type)])


@dataset_router.post("/fp-fn/cases", response_model=ApiResponse[dict])
async def create_fp_fn(
    body: FpFnCreateBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:create")),
) -> ApiResponse[dict]:
    case = ml.fp_fn.create_case(
        body.case_type, body.media_path, body.prediction,
        ground_truth=body.ground_truth, event_id=body.event_id, camera_id=body.camera_id,
    )
    return ApiResponse(data=case.to_dict())


@dataset_router.post("/fp-fn/cases/{case_id}/correct", response_model=ApiResponse[dict])
async def correct_fp_fn(
    case_id: str,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("dataset:update")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.fp_fn.mark_corrected(case_id, actor=user.get("username")).to_dict())


@dataset_router.post("/active-learning/enqueue", response_model=ApiResponse[dict])
async def enqueue_active_learning(
    body: ActiveLearningBody,
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:create")),
) -> ApiResponse[dict]:
    item = ml.active_learning.enqueue_low_confidence(
        body.item_id, body.confidence, reason=body.reason, dataset_id=body.dataset_id
    )
    return ApiResponse(data=item.to_dict() if item else {"skipped": True})


@dataset_router.get("/active-learning/queue", response_model=ApiResponse[list])
async def active_learning_queue(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[list]:
    return ApiResponse(data=[i.to_dict() for i in ml.active_learning.list_queue()])


@dataset_router.get("/active-learning/statistics", response_model=ApiResponse[dict])
async def active_learning_stats(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("dataset:read")),
) -> ApiResponse[dict]:
    return ApiResponse(data=ml.active_learning.statistics())


# Dashboard aggregate
@training_router.get("/dashboard/overview", response_model=ApiResponse[dict])
async def training_dashboard(
    ml: MLPlatformContainer = Depends(get_ml_platform),
    _: dict = Depends(require_permission("training:read")),
) -> ApiResponse[dict]:
    jobs = ml.training.list_jobs()
    running = [j for j in jobs if j.status == "running"]
    latest = jobs[0] if jobs else None
    epochs = ml.training.epoch_history(latest.id) if latest else []
    return ApiResponse(data={
        "dataset_stats": ml.datasets.statistics(),
        "active_jobs": len(running),
        "total_jobs": len(jobs),
        "latest_job": latest.to_dict() if latest else None,
        "loss_curve": ml.validation.loss_curve(epochs),
        "accuracy_curve": ml.validation.accuracy_curve(epochs),
        "active_learning": ml.active_learning.statistics(),
        "fp_fn_open": len([c for c in ml.fp_fn.list_cases() if c.status == "open"]),
    })
