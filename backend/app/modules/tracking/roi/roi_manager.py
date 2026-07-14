"""
ROIManager — quản lý nhiều vùng ROI cho một camera.

Xác định track đang ở ROI nào; hỗ trợ enter/leave/transition.
"""

from __future__ import annotations

from typing import List, Optional

from app.modules.tracking.config import ROIRegionConfig
from app.modules.tracking.exceptions import ROIError
from app.modules.tracking.models import ROI


class ROIManager:
    """Quản lý tập ROI và truy vấn vị trí điểm."""

    def __init__(self, regions: List[ROI] | None = None) -> None:
        self._regions: List[ROI] = regions or []

    @classmethod
    def from_config(cls, configs: List[ROIRegionConfig]) -> "ROIManager":
        """Tạo ROIManager từ cấu hình."""
        regions: List[ROI] = []
        for c in configs:
            if len(c.polygon) < 3:
                raise ROIError(f"ROI '{c.id}' cần >= 3 đỉnh polygon.")
            regions.append(
                ROI(
                    id=c.id,
                    name=c.name,
                    polygon=[(float(p[0]), float(p[1])) for p in c.polygon],
                    color=c.color,
                    description=c.description,
                )
            )
        return cls(regions)

    @property
    def regions(self) -> List[ROI]:
        """Danh sách ROI."""
        return self._regions

    def locate(self, x: float, y: float) -> Optional[ROI]:
        """
        Tìm ROI đầu tiên chứa điểm (x, y).

        Args:
            x, y: Tọa độ tâm track.

        Returns:
            ROI chứa điểm, hoặc None nếu không thuộc ROI nào.
        """
        for roi in self._regions:
            if roi.contains(x, y):
                return roi
        return None

    def to_dict_list(self) -> list[dict]:
        """Serialize danh sách ROI."""
        return [r.to_dict() for r in self._regions]
