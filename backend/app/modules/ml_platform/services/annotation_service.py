"""Annotation Manager Service."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.exceptions.base import NotFoundError
from app.modules.ml_platform.config.labels import LABEL_CLASSES, SUPPORTED_ANNOTATION_TOOLS
from app.modules.ml_platform.repositories.base import AnnotationRepository, DatasetItemRepository
from app.modules.ml_platform.repositories.entities import AnnotationEntity


class AnnotationService:
    """Quản lý annotation — internal + tích hợp CVAT/Label Studio/Roboflow."""

    def __init__(
        self,
        annotations: AnnotationRepository,
        items: DatasetItemRepository,
    ) -> None:
        self._annotations = annotations
        self._items = items
        self._external_config: Dict[str, Dict[str, Any]] = {}

    def label_classes(self) -> List[str]:
        return list(LABEL_CLASSES)

    def supported_tools(self) -> List[str]:
        return list(SUPPORTED_ANNOTATION_TOOLS)

    def configure_external(self, tool: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if tool not in SUPPORTED_ANNOTATION_TOOLS:
            raise ValueError(f"Tool không hỗ trợ: {tool}")
        self._external_config[tool] = config
        return {"tool": tool, "configured": True}

    def external_status(self) -> Dict[str, Any]:
        return {tool: bool(cfg) for tool, cfg in self._external_config.items()}

    def create_annotation(
        self,
        item_id: str,
        label: str,
        *,
        bbox: Optional[List[float]] = None,
        polygon: Optional[List[List[float]]] = None,
        tool: str = "internal",
        annotator: Optional[str] = None,
    ) -> AnnotationEntity:
        item = self._items.get(item_id)
        if item is None:
            raise NotFoundError("DatasetItem", item_id)
        if label not in LABEL_CLASSES:
            raise ValueError(f"Label không hợp lệ: {label}")
        entity = AnnotationEntity(
            item_id=item_id,
            label=label,
            bbox=bbox,
            polygon=polygon,
            tool=tool,
            annotator=annotator,
        )
        saved = self._annotations.save(entity)
        if label not in item.labels:
            item.labels.append(label)
        item.annotated = True
        self._items.save(item)
        return saved

    def list_annotations(self, item_id: Optional[str] = None) -> List[AnnotationEntity]:
        return self._annotations.list(item_id)

    def delete_annotation(self, annotation_id: str) -> None:
        self._annotations.delete(annotation_id)

    def export_yolo_format(self, dataset_id: str, item_ids: List[str]) -> List[Dict[str, Any]]:
        """Export annotations dạng YOLO txt."""
        exports = []
        for iid in item_ids:
            anns = self._annotations.list(iid)
            item = self._items.get(iid)
            if not item:
                continue
            lines = []
            for ann in anns:
                if ann.bbox and len(ann.bbox) == 4:
                    cls_id = LABEL_CLASSES.index(ann.label) if ann.label in LABEL_CLASSES else 0
                    x, y, w, h = ann.bbox
                    lines.append(f"{cls_id} {x} {y} {w} {h}")
            exports.append({"item_id": iid, "path": item.path, "labels": "\n".join(lines)})
        return exports

    def import_from_external(
        self,
        tool: str,
        payload: List[Dict[str, Any]],
        *,
        annotator: Optional[str] = None,
    ) -> int:
        """Import batch annotations từ tool bên ngoài."""
        count = 0
        for row in payload:
            self.create_annotation(
                row["item_id"],
                row["label"],
                bbox=row.get("bbox"),
                polygon=row.get("polygon"),
                tool=tool,
                annotator=annotator,
            )
            count += 1
        return count
