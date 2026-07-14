"""Tests for ML Platform module (Sprint 13)."""

from __future__ import annotations

import pytest

from app.modules.ml_platform.dependencies import _build_container
from app.modules.ml_platform.repositories.memory import InMemoryDatasetVersionRepository


@pytest.fixture
def ml():
    return _build_container()


def test_dataset_create_import_search(ml):
    ds = ml.datasets.create_dataset("office-v1", source_type="snapshot")
    items = ml.datasets.import_items(ds.id, ["/data/img1.jpg", "/data/img2.jpg"])
    assert len(items) == 2
    assert ml.datasets.get_dataset(ds.id).item_count == 2
    found = ml.datasets.search_items(ds.id, q="img1")
    assert len(found) == 1


def test_dataset_version_and_split(ml):
    ds = ml.datasets.create_dataset("split-test")
    ml.datasets.import_items(ds.id, [f"/img{i}.jpg" for i in range(10)])
    ver = ml.datasets.create_version(ds.id, "v1")
    splits = ml.datasets.split_dataset(ds.id, ver.id)
    assert len(splits["train"]) + len(splits["val"]) + len(splits["test"]) == 10


def test_annotation_create(ml):
    ds = ml.datasets.create_dataset("ann-test")
    items = ml.datasets.import_items(ds.id, ["/img.jpg"])
    ann = ml.annotations.create_annotation(items[0].id, "phone", bbox=[0.1, 0.2, 0.3, 0.4])
    assert ann.label == "phone"
    assert ml.annotations.list_annotations(items[0].id)


def test_label_classes(ml):
    labels = ml.annotations.label_classes()
    assert "person" in labels
    assert "phone" in labels


@pytest.mark.asyncio
async def test_training_pipeline(ml):
    ds = ml.datasets.create_dataset("train-ds")
    ml.datasets.import_items(ds.id, ["/a.jpg", "/b.jpg"])
    ver = ml.datasets.create_version(ds.id, "v1")
    job = ml.training.create_job("yolo-test", ver.id, architecture="yolo11", config={"epochs": 3})
    job = await ml.training.start_job(job.id, simulate=True)
    assert job.status == "running"
    import asyncio
    await asyncio.sleep(0.5)
    finished = ml.training.get_job(job.id)
    assert finished.status == "completed"
    epochs = ml.training.epoch_history(job.id)
    assert len(epochs) == 3
    assert finished.metrics.get("map50", 0) > 0


def test_fp_fn_and_active_learning(ml):
    case = ml.fp_fn.create_case(
        "false_positive",
        "/evidence/fp.jpg",
        {"label": "phone", "confidence": 0.9},
        ground_truth={"label": "none"},
    )
    assert case.case_type == "false_positive"
    item = ml.active_learning.enqueue_low_confidence("item-1", 0.3)
    assert item is not None
    assert ml.active_learning.statistics()["queued"] >= 1


def test_benchmark(ml):
    result = ml.benchmark.benchmark(architecture="yolo11")
    assert "fps" in result
    assert "latency_ms" in result


def test_dataset_merge(ml):
    d1 = ml.datasets.create_dataset("merge-a")
    d2 = ml.datasets.create_dataset("merge-b")
    ml.datasets.import_items(d1.id, ["/a.jpg"])
    ml.datasets.import_items(d2.id, ["/b.jpg"])
    merged = ml.datasets.merge_datasets([d1.id, d2.id], "merged-ds")
    assert merged.item_count == 2


def test_evaluation_compare(ml):
    from app.modules.ml_platform.repositories.entities import TrainingJobEntity

    jobs = [
        TrainingJobEntity(name="a", dataset_version_id="v", status="completed", metrics={"map50": 0.8, "map50_95": 0.6, "f1": 0.75}),
        TrainingJobEntity(name="b", dataset_version_id="v", status="completed", metrics={"map50": 0.7, "map50_95": 0.55, "f1": 0.7}),
    ]
    ranked = ml.evaluation.compare_jobs(jobs)
    assert ranked[0]["map50_95"] >= ranked[1]["map50_95"]
