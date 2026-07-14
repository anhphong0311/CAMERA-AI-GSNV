"""Dataset Manager Service."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from app.exceptions.base import ConflictError, NotFoundError
from app.modules.ml_platform.repositories.base import (
    DatasetItemRepository,
    DatasetRepository,
    DatasetVersionRepository,
)
from app.modules.ml_platform.repositories.entities import (
    DatasetEntity,
    DatasetItemEntity,
    DatasetVersionEntity,
)


class DatasetService:
    """Quản lý dataset: import, export, search, filter, merge, split."""

    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        items: DatasetItemRepository,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._items = items

    def list_datasets(self, *, tag: Optional[str] = None) -> List[DatasetEntity]:
        data = self._datasets.list()
        if tag:
            data = [d for d in data if tag in d.tags]
        return data

    def get_dataset(self, dataset_id: str) -> DatasetEntity:
        ds = self._datasets.get(dataset_id)
        if ds is None:
            raise NotFoundError("Dataset", dataset_id)
        return ds

    def create_dataset(
        self,
        name: str,
        *,
        description: str = "",
        source_type: str = "image",
        tags: Optional[List[str]] = None,
    ) -> DatasetEntity:
        if any(d.name == name for d in self._datasets.list()):
            raise ConflictError(f"Dataset '{name}' đã tồn tại.")
        entity = DatasetEntity(
            name=name,
            description=description,
            source_type=source_type,
            tags=tags or [],
        )
        return self._datasets.save(entity)

    def delete_dataset(self, dataset_id: str) -> None:
        self.get_dataset(dataset_id)
        for item in self._items.list(dataset_id):
            self._items.delete(item.id)
        self._datasets.delete(dataset_id)

    def import_items(
        self,
        dataset_id: str,
        paths: List[str],
        *,
        media_type: str = "image",
        version_id: Optional[str] = None,
    ) -> List[DatasetItemEntity]:
        ds = self.get_dataset(dataset_id)
        saved = []
        for path in paths:
            item = DatasetItemEntity(
                dataset_id=dataset_id,
                path=path,
                media_type=media_type,
                version_id=version_id,
            )
            saved.append(self._items.save(item))
        ds.item_count = len(self._items.list(dataset_id))
        self._datasets.save(ds)
        return saved

    def search_items(
        self,
        dataset_id: str,
        *,
        annotated: Optional[bool] = None,
        label: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[DatasetItemEntity]:
        items = self._items.list(dataset_id, annotated=annotated, label=label)
        if q:
            q_lower = q.lower()
            items = [i for i in items if q_lower in i.path.lower()]
        return items

    def create_version(
        self,
        dataset_id: str,
        version: str,
        *,
        split_train: float = 0.8,
        split_val: float = 0.1,
        split_test: float = 0.1,
        notes: str = "",
    ) -> DatasetVersionEntity:
        self.get_dataset(dataset_id)
        entity = DatasetVersionEntity(
            dataset_id=dataset_id,
            version=version,
            split_train=split_train,
            split_val=split_val,
            split_test=split_test,
            item_count=len(self._items.list(dataset_id)),
            notes=notes,
        )
        return self._versions.save(entity)

    def list_versions(self, dataset_id: str) -> List[DatasetVersionEntity]:
        return self._versions.list(dataset_id)

    def split_dataset(
        self,
        dataset_id: str,
        version_id: str,
    ) -> Dict[str, List[str]]:
        """Gán split train/val/test cho items."""
        ver = self._versions.get(version_id)
        if ver is None or ver.dataset_id != dataset_id:
            raise NotFoundError("DatasetVersion", version_id)
        items = self._items.list(dataset_id)
        random.shuffle(items)
        n = len(items)
        n_train = int(n * ver.split_train)
        n_val = int(n * ver.split_val)
        splits = {
            "train": [i.id for i in items[:n_train]],
            "val": [i.id for i in items[n_train : n_train + n_val]],
            "test": [i.id for i in items[n_train + n_val :]],
        }
        for item in items:
            item.version_id = version_id
            self._items.save(item)
        return splits

    def merge_datasets(self, source_ids: List[str], target_name: str) -> DatasetEntity:
        target = self.create_dataset(target_name, description="Merged dataset")
        for sid in source_ids:
            for item in self._items.list(sid):
                clone = DatasetItemEntity(
                    dataset_id=target.id,
                    path=item.path,
                    media_type=item.media_type,
                    labels=list(item.labels),
                    metadata=dict(item.metadata),
                    annotated=item.annotated,
                )
                self._items.save(clone)
        target.item_count = len(self._items.list(target.id))
        return self._datasets.save(target)

    def export_manifest(self, dataset_id: str) -> Dict[str, Any]:
        ds = self.get_dataset(dataset_id)
        items = self._items.list(dataset_id)
        return {
            "dataset": ds.to_dict(),
            "items": [i.to_dict() for i in items],
            "versions": [v.to_dict() for v in self._versions.list(dataset_id)],
        }

    def statistics(self) -> Dict[str, Any]:
        datasets = self._datasets.list()
        total_items = sum(len(self._items.list(d.id)) for d in datasets)
        annotated = sum(
            len(self._items.list(d.id, annotated=True)) for d in datasets
        )
        return {
            "datasets": len(datasets),
            "total_items": total_items,
            "annotated_items": annotated,
            "annotation_rate": round(annotated / total_items * 100, 1) if total_items else 0,
        }
