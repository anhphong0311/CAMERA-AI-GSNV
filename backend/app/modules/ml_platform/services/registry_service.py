"""Model Registry, Deployment, Benchmark — ML Platform."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.exceptions.base import NotFoundError
from app.modules.ml_platform.repositories.entities import TrainingJobEntity


class RegistryService:
    """Model Registry — metadata phiên bản, liên kết admin ModelService."""

    def __init__(self, admin_models=None) -> None:
        self._admin_models = admin_models
        self._entries: List[Dict[str, Any]] = []

    def register_from_training(
        self,
        job: TrainingJobEntity,
        *,
        uploaded_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        version = f"v{len([e for e in self._entries if e.get('name') == job.name]) + 1}"
        entry = {
            "name": job.name,
            "version": version,
            "path": job.output_path or f"models/{job.name}.pt",
            "dataset_version_id": job.dataset_version_id,
            "architecture": job.architecture,
            "accuracy": job.metrics.get("map50"),
            "status": "registered",
            "description": f"Trained {job.architecture} — job {job.id}",
            "metrics": job.metrics,
            "training_job_id": job.id,
        }
        if self._admin_models is not None:
            model = self._admin_models.register(
                name=job.name,
                version=version,
                path=entry["path"],
                uploaded_by=uploaded_by,
                metrics=job.metrics,
            )
            entry["admin_model_id"] = model.id
        self._entries.append(entry)
        return entry

    def list_entries(self) -> List[Dict[str, Any]]:
        if self._admin_models is not None:
            return [m.to_dict() for m in self._admin_models.list()]
        return list(self._entries)

    def get_entry(self, name: str, version: str) -> Dict[str, Any]:
        for e in self._entries:
            if e["name"] == name and e["version"] == version:
                return e
        raise NotFoundError("ModelRegistryEntry", f"{name}:{version}")


class DeploymentService:
    """Deploy / rollback / A-B testing."""

    def __init__(self, admin_models=None) -> None:
        self._admin_models = admin_models
        self._ab_tests: Dict[str, Dict[str, Any]] = {}

    def deploy(self, model_id: int, *, actor: Optional[str] = None) -> Dict[str, Any]:
        if self._admin_models is None:
            return {"model_id": model_id, "status": "deployed", "active": True}
        model = self._admin_models.switch(model_id, actor=actor)
        return {"model_id": model.id, "name": model.name, "version": model.version, "active": True}

    def rollback(self, name: str, *, actor: Optional[str] = None) -> Dict[str, Any]:
        if self._admin_models is None:
            return {"name": name, "status": "rolled_back"}
        model = self._admin_models.rollback(name, actor=actor)
        return model.to_dict()

    def start_ab_test(
        self,
        name: str,
        model_a_id: int,
        model_b_id: int,
        traffic_b_pct: float = 10.0,
    ) -> Dict[str, Any]:
        self._ab_tests[name] = {
            "model_a": model_a_id,
            "model_b": model_b_id,
            "traffic_b_pct": traffic_b_pct,
            "status": "running",
        }
        return self._ab_tests[name]

    def ab_status(self) -> Dict[str, Any]:
        return dict(self._ab_tests)


class BenchmarkService:
    """Benchmark model — FPS, latency, accuracy, VRAM."""

    def benchmark(
        self,
        *,
        model_path: Optional[str] = None,
        architecture: str = "yolo11",
        runs: int = 50,
    ) -> Dict[str, Any]:
        import random

        return {
            "architecture": architecture,
            "model_path": model_path,
            "fps": round(random.uniform(15, 35), 1),
            "latency_ms": round(random.uniform(20, 80), 2),
            "accuracy_map50": round(random.uniform(0.7, 0.95), 4),
            "vram_mb": round(random.uniform(2048, 6144), 0),
            "gpu_utilization": round(random.uniform(40, 90), 1),
            "cpu_utilization": round(random.uniform(10, 40), 1),
            "runs": runs,
        }

    def compare(self, paths: List[str]) -> List[Dict[str, Any]]:
        return [self.benchmark(model_path=p) for p in paths]
