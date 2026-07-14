"""InMemory repositories — ML Platform (default/test)."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.modules.ml_platform.repositories.base import (
    ActiveLearningRepository,
    AnnotationRepository,
    DatasetItemRepository,
    DatasetRepository,
    DatasetVersionRepository,
    FpFnRepository,
    TrainingEpochRepository,
    TrainingJobRepository,
)
from app.modules.ml_platform.repositories.entities import (
    ActiveLearningItemEntity,
    AnnotationEntity,
    DatasetEntity,
    DatasetItemEntity,
    DatasetVersionEntity,
    FpFnCaseEntity,
    TrainingEpochEntity,
    TrainingJobEntity,
)


class InMemoryDatasetRepository(DatasetRepository):
    def __init__(self) -> None:
        self._data: Dict[str, DatasetEntity] = {}

    def list(self) -> List[DatasetEntity]:
        return list(self._data.values())

    def get(self, dataset_id: str) -> Optional[DatasetEntity]:
        return self._data.get(dataset_id)

    def save(self, entity: DatasetEntity) -> DatasetEntity:
        self._data[entity.id] = entity
        return entity

    def delete(self, dataset_id: str) -> None:
        self._data.pop(dataset_id, None)


class InMemoryDatasetVersionRepository(DatasetVersionRepository):
    def __init__(self) -> None:
        self._data: Dict[str, DatasetVersionEntity] = {}

    def list(self, dataset_id: Optional[str] = None) -> List[DatasetVersionEntity]:
        items = list(self._data.values())
        if dataset_id:
            items = [v for v in items if v.dataset_id == dataset_id]
        return items

    def get(self, version_id: str) -> Optional[DatasetVersionEntity]:
        return self._data.get(version_id)

    def save(self, entity: DatasetVersionEntity) -> DatasetVersionEntity:
        self._data[entity.id] = entity
        return entity


class InMemoryDatasetItemRepository(DatasetItemRepository):
    def __init__(self) -> None:
        self._data: Dict[str, DatasetItemEntity] = {}

    def list(
        self,
        dataset_id: Optional[str] = None,
        *,
        annotated: Optional[bool] = None,
        label: Optional[str] = None,
    ) -> List[DatasetItemEntity]:
        items = list(self._data.values())
        if dataset_id:
            items = [i for i in items if i.dataset_id == dataset_id]
        if annotated is not None:
            items = [i for i in items if i.annotated == annotated]
        if label:
            items = [i for i in items if label in i.labels]
        return items

    def get(self, item_id: str) -> Optional[DatasetItemEntity]:
        return self._data.get(item_id)

    def save(self, entity: DatasetItemEntity) -> DatasetItemEntity:
        self._data[entity.id] = entity
        return entity

    def delete(self, item_id: str) -> None:
        self._data.pop(item_id, None)


class InMemoryAnnotationRepository(AnnotationRepository):
    def __init__(self) -> None:
        self._data: Dict[str, AnnotationEntity] = {}

    def list(self, item_id: Optional[str] = None) -> List[AnnotationEntity]:
        items = list(self._data.values())
        if item_id:
            items = [a for a in items if a.item_id == item_id]
        return items

    def save(self, entity: AnnotationEntity) -> AnnotationEntity:
        self._data[entity.id] = entity
        return entity

    def delete(self, annotation_id: str) -> None:
        self._data.pop(annotation_id, None)


class InMemoryTrainingJobRepository(TrainingJobRepository):
    def __init__(self) -> None:
        self._data: Dict[str, TrainingJobEntity] = {}

    def list(self) -> List[TrainingJobEntity]:
        return list(self._data.values())

    def get(self, job_id: str) -> Optional[TrainingJobEntity]:
        return self._data.get(job_id)

    def save(self, entity: TrainingJobEntity) -> TrainingJobEntity:
        self._data[entity.id] = entity
        return entity


class InMemoryTrainingEpochRepository(TrainingEpochRepository):
    def __init__(self) -> None:
        self._data: Dict[str, TrainingEpochEntity] = {}

    def list(self, job_id: str) -> List[TrainingEpochEntity]:
        return sorted(
            [e for e in self._data.values() if e.job_id == job_id],
            key=lambda e: e.epoch,
        )

    def save(self, entity: TrainingEpochEntity) -> TrainingEpochEntity:
        self._data[entity.id] = entity
        return entity


class InMemoryFpFnRepository(FpFnRepository):
    def __init__(self) -> None:
        self._data: Dict[str, FpFnCaseEntity] = {}

    def list(self, case_type: Optional[str] = None) -> List[FpFnCaseEntity]:
        items = list(self._data.values())
        if case_type:
            items = [c for c in items if c.case_type == case_type]
        return items

    def get(self, case_id: str) -> Optional[FpFnCaseEntity]:
        return self._data.get(case_id)

    def save(self, entity: FpFnCaseEntity) -> FpFnCaseEntity:
        self._data[entity.id] = entity
        return entity


class InMemoryActiveLearningRepository(ActiveLearningRepository):
    def __init__(self) -> None:
        self._data: Dict[str, ActiveLearningItemEntity] = {}

    def list(self, status: Optional[str] = None) -> List[ActiveLearningItemEntity]:
        items = list(self._data.values())
        if status:
            items = [i for i in items if i.status == status]
        return items

    def save(self, entity: ActiveLearningItemEntity) -> ActiveLearningItemEntity:
        self._data[entity.id] = entity
        return entity

    def delete(self, item_id: str) -> None:
        for k, v in list(self._data.items()):
            if v.id == item_id:
                del self._data[k]
                return
