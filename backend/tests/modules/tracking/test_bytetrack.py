"""
Unit tests — ByteTrack: matching (Hungarian), IoU, tracker ID stability & recovery.
"""

import numpy as np

from app.modules.tracking.bytetrack.matching import (
    bbox_ious,
    iou_distance,
    linear_assignment,
)
from app.modules.tracking.config import TrackerConfig
from app.modules.tracking.tracking_engine.base_tracker import DetectionInput
from app.modules.tracking.bytetrack.adapter import ByteTrackAdapter


class TestMatching:
    """Test hàm matching."""

    def test_bbox_ious_identical(self) -> None:
        """IoU box trùng = 1."""
        a = np.array([[0, 0, 10, 10]], dtype=np.float32)
        ious = bbox_ious(a, a)
        assert ious[0, 0] == 1.0

    def test_bbox_ious_disjoint(self) -> None:
        """IoU box tách rời = 0."""
        a = np.array([[0, 0, 10, 10]], dtype=np.float32)
        b = np.array([[20, 20, 30, 30]], dtype=np.float32)
        assert bbox_ious(a, b)[0, 0] == 0.0

    def test_linear_assignment_optimal(self) -> None:
        """Hungarian chọn gán tổng cost nhỏ nhất."""
        cost = np.array([[0.1, 0.9], [0.9, 0.2]], dtype=np.float32)
        matches, ua, ub = linear_assignment(cost, thresh=0.8)
        assert (0, 0) in matches
        assert (1, 1) in matches
        assert ua == [] and ub == []

    def test_linear_assignment_threshold(self) -> None:
        """Cặp vượt thresh bị loại thành unmatched."""
        cost = np.array([[0.1, 0.95], [0.95, 0.95]], dtype=np.float32)
        matches, ua, ub = linear_assignment(cost, thresh=0.8)
        assert (0, 0) in matches
        assert 1 in ua  # track 1 không match được

    def test_linear_assignment_empty(self) -> None:
        """Ma trận rỗng → không match."""
        cost = np.zeros((0, 3), dtype=np.float32)
        matches, ua, ub = linear_assignment(cost, thresh=0.8)
        assert matches == []
        assert ub == [0, 1, 2]

    def test_linear_assignment_rectangular(self) -> None:
        """Nhiều detection hơn track — track được gán tối ưu."""
        cost = np.array([[0.1, 0.5, 0.9]], dtype=np.float32)
        matches, ua, ub = linear_assignment(cost, thresh=0.8)
        assert (0, 0) in matches
        assert set(ub) == {1, 2}


class TestByteTrackAdapter:
    """Test tracker ID ổn định và phục hồi."""

    def _adapter(self) -> ByteTrackAdapter:
        return ByteTrackAdapter(TrackerConfig(min_box_area=10.0))

    def test_stable_ids_across_frames(self) -> None:
        """2 người di chuyển → ID giữ nguyên qua nhiều frame."""
        adapter = self._adapter()
        ids_per_frame = []
        for f in range(10):
            dets = [
                DetectionInput((10 + f * 2, 10, 50 + f * 2, 110), 0.9, 0, "person"),
                DetectionInput((300 + f * 2, 200, 340 + f * 2, 300), 0.9, 0, "person"),
            ]
            out = adapter.update(dets)
            ids_per_frame.append(sorted(o.track_id for o in out))
        # Sau khi ổn định (frame >=2), ID không đổi
        assert ids_per_frame[-1] == ids_per_frame[-2]
        assert len(ids_per_frame[-1]) == 2

    def test_recovery_same_id_after_occlusion(self) -> None:
        """Người biến mất vài frame rồi quay lại → giữ nguyên ID (recovery)."""
        adapter = self._adapter()
        # Thiết lập track ổn định
        for f in range(5):
            adapter.update(
                [DetectionInput((10 + f * 2, 10, 50 + f * 2, 110), 0.9, 0, "person")]
            )
        out = adapter.update(
            [DetectionInput((20, 10, 60, 110), 0.9, 0, "person")]
        )
        original_id = out[0].track_id

        # Mất 3 frame (không có detection)
        for _ in range(3):
            adapter.update([])

        # Quay lại gần vị trí cũ
        out = adapter.update([DetectionInput((26, 10, 66, 110), 0.9, 0, "person")])
        assert len(out) == 1
        assert out[0].track_id == original_id

    def test_iou_distance_shape(self) -> None:
        """iou_distance trả ma trận đúng chiều."""

        class _T:
            def __init__(self, tlbr):
                self.tlbr = np.array(tlbr, dtype=np.float32)

        a = [_T([0, 0, 10, 10]), _T([5, 5, 15, 15])]
        b = [_T([0, 0, 10, 10])]
        d = iou_distance(a, b)
        assert d.shape == (2, 1)
        assert d[0, 0] == 0.0  # trùng hoàn toàn → distance 0
