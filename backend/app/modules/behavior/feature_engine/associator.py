"""
PoseAssociator — gán khung pose (người) với track theo IoU.

Tracking Engine đã cho track_id ổn định; pose model cho khung + skeleton.
Ta ghép chúng lại để mỗi track có skeleton tương ứng.
"""

from __future__ import annotations

from typing import Dict, List

from app.modules.behavior.models import PoseResult
from app.modules.behavior.utils.geometry import bbox_iou


class PoseAssociator:
    """Ghép PoseResult ↔ Track bằng IoU (greedy)."""

    def __init__(self, iou_threshold: float = 0.3) -> None:
        self._iou_threshold = iou_threshold

    def associate(
        self, tracks: List, poses: List[PoseResult]
    ) -> Dict[int, PoseResult]:
        """
        Gán pose cho track.

        Args:
            tracks: Danh sách Track (có .track_id, .bbox).
            poses: Danh sách PoseResult.

        Returns:
            dict track_id → PoseResult (chỉ track khớp trên ngưỡng).
        """
        result: Dict[int, PoseResult] = {}
        used: set[int] = set()
        for track in tracks:
            best_idx = -1
            best_iou = self._iou_threshold
            for idx, pose in enumerate(poses):
                if idx in used:
                    continue
                iou = bbox_iou(tuple(track.bbox), pose.bbox)
                if iou >= best_iou:
                    best_iou = iou
                    best_idx = idx
            if best_idx >= 0:
                result[track.track_id] = poses[best_idx]
                used.add(best_idx)
        return result
