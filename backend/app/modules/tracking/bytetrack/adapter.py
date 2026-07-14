"""
ByteTrackAdapter — bọc BYTETracker theo interface BaseTracker.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from app.modules.tracking.bytetrack.byte_tracker import BYTETracker
from app.modules.tracking.config import TrackerConfig
from app.modules.tracking.models import TrackedObject
from app.modules.tracking.tracking_engine.base_tracker import (
    BaseTracker,
    DetectionInput,
)


class ByteTrackAdapter(BaseTracker):
    """Adapter ByteTrack — chuyển DetectionInput ↔ TrackedObject."""

    def __init__(self, config: TrackerConfig) -> None:
        self._config = config
        self._tracker = BYTETracker(config)
        self._class_names: dict[int, str] = {}

    @property
    def name(self) -> str:
        """Tên thuật toán."""
        return "bytetrack"

    def update(self, detections: Sequence[DetectionInput]) -> List[TrackedObject]:
        """Chạy một bước ByteTrack và trả TrackedObject."""
        if detections:
            boxes = np.array([d.xyxy for d in detections], dtype=np.float32)
            scores = np.array([d.score for d in detections], dtype=np.float32)
            classes = np.array([d.class_id for d in detections], dtype=np.int32)
            for d in detections:
                self._class_names[d.class_id] = d.class_name
        else:
            boxes = np.empty((0, 4), dtype=np.float32)
            scores = np.empty((0,), dtype=np.float32)
            classes = np.empty((0,), dtype=np.int32)

        stracks = self._tracker.update(boxes, scores, classes)

        results: List[TrackedObject] = []
        for st in stracks:
            x1, y1, x2, y2 = (float(v) for v in st.tlbr)
            if (x2 - x1) * (y2 - y1) < self._config.min_box_area:
                continue
            results.append(
                TrackedObject(
                    track_id=st.track_id,
                    xyxy=(x1, y1, x2, y2),
                    score=st.score,
                    class_id=st.cls,
                    class_name=self._class_names.get(st.cls, "person"),
                )
            )
        return results

    def reset(self) -> None:
        """Reset tracker (tạo BYTETracker mới)."""
        self._tracker = BYTETracker(self._config)
