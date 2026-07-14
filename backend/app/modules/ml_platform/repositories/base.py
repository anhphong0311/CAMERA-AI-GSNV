"""Repository ABCs — ML Platform."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

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


class DatasetRepository(ABC):
    @abstractmethod
    def list(self) -> List[DatasetEntity]: ...

    @abstractmethod
    def get(self, dataset_id: str) -> Optional[DatasetEntity]: ...

    @abstractmethod
    def save(self, entity: DatasetEntity) -> DatasetEntity: ...

    @abstractmethod
    def delete(self, dataset_id: str) -> None: ...


class DatasetVersionRepository(ABC):
    @abstractmethod
    def list(self, dataset_id: Optional[str] = None) -> List[DatasetVersionEntity]: ...

    @abstractmethod
    def get(self, version_id: str) -> Optional[DatasetVersionEntity]: ...

    @abstractmethod
    def save(self, entity: DatasetVersionEntity) -> DatasetVersionEntity: ...


class DatasetItemRepository(ABC):
    @abstractmethod
    def list(
        self,
        dataset_id: Optional[str] = None,
        *,
        annotated: Optional[bool] = None,
        label: Optional[str] = None,
    ) -> List[DatasetItemEntity]: ...

    @abstractmethod
    def get(self, item_id: str) -> Optional[DatasetItemEntity]: ...

    @abstractmethod
    def save(self, entity: DatasetItemEntity) -> DatasetItemEntity: ...

    @abstractmethod
    def delete(self, item_id: str) -> None: ...


class AnnotationRepository(ABC):
    @abstractmethod
    def list(self, item_id: Optional[str] = None) -> List[AnnotationEntity]: ...

    @abstractmethod
    def save(self, entity: AnnotationEntity) -> AnnotationEntity: ...

    @abstractmethod
    def delete(self, annotation_id: str) -> None: ...


class TrainingJobRepository(ABC):
    @abstractmethod
    def list(self) -> List[TrainingJobEntity]: ...

    @abstractmethod
    def get(self, job_id: str) -> Optional[TrainingJobEntity]: ...

    @abstractmethod
    def save(self, entity: TrainingJobEntity) -> TrainingJobEntity: ...


class TrainingEpochRepository(ABC):
    @abstractmethod
    def list(self, job_id: str) -> List[TrainingEpochEntity]: ...

    @abstractmethod
    def save(self, entity: TrainingEpochEntity) -> TrainingEpochEntity: ...


class FpFnRepository(ABC):
    @abstractmethod
    def list(self, case_type: Optional[str] = None) -> List[FpFnCaseEntity]: ...

    @abstractmethod
    def get(self, case_id: str) -> Optional[FpFnCaseEntity]: ...

    @abstractmethod
    def save(self, entity: FpFnCaseEntity) -> FpFnCaseEntity: ...


class ActiveLearningRepository(ABC):
    @abstractmethod
    def list(self, status: Optional[str] = None) -> List[ActiveLearningItemEntity]: ...

    @abstractmethod
    def save(self, entity: ActiveLearningItemEntity) -> ActiveLearningItemEntity: ...

    @abstractmethod
    def delete(self, item_id: str) -> None: ...
