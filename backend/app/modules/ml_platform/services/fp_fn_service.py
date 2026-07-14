"""False Positive/Negative Center & Active Learning."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.exceptions.base import NotFoundError
from app.modules.ml_platform.repositories.base import (
    ActiveLearningRepository,
    DatasetItemRepository,
    FpFnRepository,
)
from app.modules.ml_platform.repositories.entities import (
    ActiveLearningItemEntity,
    DatasetItemEntity,
    FpFnCaseEntity,
)


class FpFnService:
    """False Positive / False Negative review center."""

    def __init__(
        self,
        cases: FpFnRepository,
        items: DatasetItemRepository,
        dataset_id: Optional[str] = None,
    ) -> None:
        self._cases = cases
        self._items = items
        self._training_dataset_id = dataset_id

    def list_cases(self, case_type: Optional[str] = None) -> List[FpFnCaseEntity]:
        return self._cases.list(case_type)

    def create_case(
        self,
        case_type: str,
        media_path: str,
        prediction: Dict[str, Any],
        *,
        ground_truth: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        camera_id: Optional[int] = None,
    ) -> FpFnCaseEntity:
        entity = FpFnCaseEntity(
            case_type=case_type,
            media_path=media_path,
            prediction=prediction,
            ground_truth=ground_truth,
            event_id=event_id,
            camera_id=camera_id,
        )
        return self._cases.save(entity)

    def mark_corrected(self, case_id: str, *, actor: Optional[str] = None) -> FpFnCaseEntity:
        case = self._cases.get(case_id)
        if case is None:
            raise NotFoundError("FpFnCase", case_id)
        case.status = "corrected"
        case.marked_by = actor
        return self._cases.save(case)

    def add_to_training(self, case_id: str, dataset_id: str) -> DatasetItemEntity:
        case = self._cases.get(case_id)
        if case is None:
            raise NotFoundError("FpFnCase", case_id)
        item = DatasetItemEntity(
            dataset_id=dataset_id,
            path=case.media_path,
            media_type="image",
            metadata={"case_id": case_id, "case_type": case.case_type},
            annotated=case.ground_truth is not None,
        )
        case.status = "added_to_training"
        self._cases.save(case)
        return self._items.save(item)


class ActiveLearningService:
    """Đưa sample confidence thấp vào training queue."""

    CONFIDENCE_THRESHOLD = 0.45

    def __init__(self, queue: ActiveLearningRepository, items: DatasetItemRepository) -> None:
        self._queue = queue
        self._items = items

    def enqueue_low_confidence(
        self,
        item_id: str,
        confidence: float,
        *,
        reason: str = "low_confidence",
        dataset_id: Optional[str] = None,
    ) -> Optional[ActiveLearningItemEntity]:
        if confidence >= self.CONFIDENCE_THRESHOLD:
            return None
        entity = ActiveLearningItemEntity(
            item_id=item_id,
            confidence=confidence,
            reason=reason,
            dataset_id=dataset_id,
            status="queued",
        )
        return self._queue.save(entity)

    def list_queue(self, status: str = "queued") -> List[ActiveLearningItemEntity]:
        return self._queue.list(status)

    def mark_reviewed(self, queue_id: str) -> ActiveLearningItemEntity:
        items = self._queue.list()
        for item in items:
            if item.id == queue_id:
                item.status = "reviewed"
                return self._queue.save(item)
        raise NotFoundError("ActiveLearningItem", queue_id)

    def statistics(self) -> Dict[str, Any]:
        queued = self._queue.list("queued")
        reviewed = self._queue.list("reviewed")
        return {"queued": len(queued), "reviewed": len(reviewed), "threshold": self.CONFIDENCE_THRESHOLD}
