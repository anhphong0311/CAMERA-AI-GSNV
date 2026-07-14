"""
ImagePostprocessor — xử lý sau inference.

Chức năng:
- Class filter: chỉ giữ class được phép.
- Confidence filter: áp ngưỡng riêng theo từng class.
- NMS: loại box trùng lặp (cho backend raw không tự NMS).
- Coordinate mapping: map tọa độ từ không gian letterbox về ảnh gốc.
- Build Detection DTO chuẩn.

Backend Ultralytics đã NMS + map tọa độ nội bộ; postprocess ở đây vẫn cần
để áp NGƯỠNG CONFIDENCE RIÊNG THEO CLASS (ultralytics chỉ nhận 1 ngưỡng chung),
lọc class và dựng DTO chuẩn.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from app.modules.ai.models import BoundingBox, Detection, RawDetection
from app.modules.ai.preprocess.preprocessor import LetterboxMeta


class ImagePostprocessor:
    """
    Bộ hậu xử lý — chuyển RawDetection → Detection DTO.

    Attributes:
        class_map: {coco_id: (label, confidence_threshold)}.
        max_detections: Giới hạn số detection giữ lại.
    """

    def __init__(
        self,
        class_map: Dict[int, Tuple[str, float]],
        max_detections: int = 100,
    ) -> None:
        self._class_map = class_map
        self._max_detections = max_detections

    def filter_by_class(self, raws: Sequence[RawDetection]) -> List[RawDetection]:
        """
        Giữ lại chỉ các detection thuộc class cho phép.

        Args:
            raws: Danh sách RawDetection.

        Returns:
            List đã lọc theo class_map.
        """
        return [r for r in raws if r.class_id in self._class_map]

    def filter_by_confidence(self, raws: Sequence[RawDetection]) -> List[RawDetection]:
        """
        Áp ngưỡng confidence riêng cho từng class.

        Args:
            raws: Danh sách RawDetection (đã lọc class).

        Returns:
            List thỏa ngưỡng theo từng class.
        """
        result: List[RawDetection] = []
        for r in raws:
            entry = self._class_map.get(r.class_id)
            if entry is None:
                continue
            _, threshold = entry
            if r.confidence >= threshold:
                result.append(r)
        return result

    @staticmethod
    def nms(
        raws: Sequence[RawDetection],
        iou_threshold: float = 0.45,
    ) -> List[RawDetection]:
        """
        Non-Maximum Suppression theo từng class (class-aware).

        Dùng cho backend raw (ONNX/TensorRT). Backend Ultralytics đã NMS sẵn.

        Args:
            raws: Danh sách RawDetection.
            iou_threshold: Ngưỡng IoU để loại box trùng.

        Returns:
            List sau NMS.
        """
        if not raws:
            return []

        kept: List[RawDetection] = []
        # NMS riêng cho từng class_id
        by_class: Dict[int, List[RawDetection]] = {}
        for r in raws:
            by_class.setdefault(r.class_id, []).append(r)

        for _, group in by_class.items():
            group_sorted = sorted(group, key=lambda d: d.confidence, reverse=True)
            while group_sorted:
                best = group_sorted.pop(0)
                kept.append(best)
                group_sorted = [
                    d
                    for d in group_sorted
                    if ImagePostprocessor._iou(best.xyxy, d.xyxy) < iou_threshold
                ]
        return kept

    @staticmethod
    def _iou(
        box_a: Tuple[float, float, float, float],
        box_b: Tuple[float, float, float, float],
    ) -> float:
        """Tính Intersection-over-Union giữa 2 box xyxy."""
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter = inter_w * inter_h
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    @staticmethod
    def map_coords_to_original(
        xyxy: Tuple[float, float, float, float],
        meta: LetterboxMeta,
    ) -> Tuple[float, float, float, float]:
        """
        Map tọa độ từ không gian letterbox về ảnh gốc.

        Dùng cho backend raw (ONNX/TensorRT). Backend Ultralytics map sẵn.

        Args:
            xyxy: Tọa độ trong ảnh letterbox.
            meta: Metadata letterbox.

        Returns:
            Tọa độ (x1,y1,x2,y2) trong ảnh gốc, đã clamp biên.
        """
        x1, y1, x2, y2 = xyxy
        x1 = (x1 - meta.pad_w) / meta.ratio
        y1 = (y1 - meta.pad_h) / meta.ratio
        x2 = (x2 - meta.pad_w) / meta.ratio
        y2 = (y2 - meta.pad_h) / meta.ratio
        # Clamp trong khung ảnh gốc
        x1 = float(np.clip(x1, 0, meta.orig_w))
        y1 = float(np.clip(y1, 0, meta.orig_h))
        x2 = float(np.clip(x2, 0, meta.orig_w))
        y2 = float(np.clip(y2, 0, meta.orig_h))
        return x1, y1, x2, y2

    def build_detections(self, raws: Sequence[RawDetection]) -> List[Detection]:
        """
        Chuyển RawDetection (đã ở tọa độ gốc) → Detection DTO.

        Args:
            raws: Danh sách RawDetection.

        Returns:
            List Detection với nhãn logic + bbox.
        """
        detections: List[Detection] = []
        for r in raws:
            entry = self._class_map.get(r.class_id)
            if entry is None:
                continue
            label, _ = entry
            detections.append(
                Detection(
                    class_name=label,
                    confidence=r.confidence,
                    bbox=BoundingBox(*r.xyxy),
                    class_id=r.class_id,
                )
            )
        return detections

    def process(
        self,
        raws: Sequence[RawDetection],
        apply_nms: bool = False,
        iou_threshold: float = 0.45,
    ) -> List[Detection]:
        """
        Pipeline hậu xử lý đầy đủ.

        Thứ tự: class filter → confidence filter → (NMS tùy chọn)
        → sort theo confidence → cắt max_detections → build DTO.

        Args:
            raws: RawDetection ở tọa độ ảnh gốc.
            apply_nms: Bật NMS thủ công (backend raw). Ultralytics để False.
            iou_threshold: Ngưỡng IoU khi NMS.

        Returns:
            List Detection cuối cùng.
        """
        filtered = self.filter_by_class(raws)
        filtered = self.filter_by_confidence(filtered)
        if apply_nms:
            filtered = self.nms(filtered, iou_threshold)
        filtered = sorted(filtered, key=lambda d: d.confidence, reverse=True)
        filtered = filtered[: self._max_detections]
        return self.build_detections(filtered)
