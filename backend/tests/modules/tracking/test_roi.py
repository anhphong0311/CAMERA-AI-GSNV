"""
Unit tests — ROI (point-in-polygon) và ROIManager.
"""

import pytest

from app.modules.tracking.config import ROIRegionConfig
from app.modules.tracking.exceptions import ROIError
from app.modules.tracking.models import ROI
from app.modules.tracking.roi.roi_manager import ROIManager


class TestROIContains:
    """Test point-in-polygon."""

    def _square(self) -> ROI:
        return ROI("r1", "Square", [(0, 0), (100, 0), (100, 100), (0, 100)])

    def test_point_inside(self) -> None:
        """Điểm trong polygon."""
        assert self._square().contains(50, 50) is True

    def test_point_outside(self) -> None:
        """Điểm ngoài polygon."""
        assert self._square().contains(150, 50) is False

    def test_degenerate_polygon(self) -> None:
        """Polygon < 3 đỉnh luôn False."""
        roi = ROI("r", "line", [(0, 0), (10, 10)])
        assert roi.contains(5, 5) is False


class TestROIManager:
    """Test ROIManager."""

    def test_from_config_and_locate(self) -> None:
        """Tạo từ config và định vị điểm."""
        cfg = ROIRegionConfig(
            id="desk", name="Desk", polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )
        mgr = ROIManager.from_config([cfg])
        roi = mgr.locate(50, 50)
        assert roi is not None
        assert roi.id == "desk"

    def test_locate_none_outside(self) -> None:
        """Điểm ngoài mọi ROI → None."""
        cfg = ROIRegionConfig(
            id="desk", name="Desk", polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )
        mgr = ROIManager.from_config([cfg])
        assert mgr.locate(500, 500) is None

    def test_invalid_polygon_raises(self) -> None:
        """Polygon < 3 đỉnh → ROIError."""
        cfg = ROIRegionConfig(id="bad", name="Bad", polygon=[[0, 0], [1, 1]])
        with pytest.raises(ROIError):
            ROIManager.from_config([cfg])

    def test_first_match_wins(self) -> None:
        """Điểm thuộc nhiều ROI → trả ROI đầu tiên."""
        c1 = ROIRegionConfig(
            id="a", name="A", polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )
        c2 = ROIRegionConfig(
            id="b", name="B", polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )
        mgr = ROIManager.from_config([c1, c2])
        assert mgr.locate(50, 50).id == "a"
