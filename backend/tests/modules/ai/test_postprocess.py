"""
Unit tests — ImagePostprocessor (class filter, confidence, NMS, coord map).
"""

from app.modules.ai.models import RawDetection
from app.modules.ai.postprocess import ImagePostprocessor
from app.modules.ai.preprocess.preprocessor import LetterboxMeta

# class_map: person(0)@0.5, phone(67)@0.65, cup(41)@0.5
CLASS_MAP = {0: ("person", 0.5), 67: ("phone", 0.65), 41: ("cup", 0.5)}


class TestPostprocessFilters:
    """Test lọc class + confidence."""

    def test_filter_by_class_drops_unknown(self) -> None:
        """Class ngoài map bị loại."""
        post = ImagePostprocessor(CLASS_MAP)
        raws = [
            RawDetection(0, 0.9, (0, 0, 10, 10)),
            RawDetection(99, 0.9, (0, 0, 10, 10)),  # không cho phép
        ]
        kept = post.filter_by_class(raws)
        assert len(kept) == 1
        assert kept[0].class_id == 0

    def test_per_class_confidence(self) -> None:
        """Phone conf 0.6 < ngưỡng 0.65 → loại; person 0.6 >= 0.5 → giữ."""
        post = ImagePostprocessor(CLASS_MAP)
        raws = [
            RawDetection(67, 0.60, (0, 0, 10, 10)),
            RawDetection(0, 0.60, (0, 0, 10, 10)),
        ]
        kept = post.filter_by_confidence(post.filter_by_class(raws))
        ids = [r.class_id for r in kept]
        assert 0 in ids
        assert 67 not in ids

    def test_max_detections_cap(self) -> None:
        """process cắt theo max_detections."""
        post = ImagePostprocessor(CLASS_MAP, max_detections=2)
        raws = [RawDetection(0, 0.9 - i * 0.01, (0, 0, 10, 10)) for i in range(5)]
        dets = post.process(raws)
        assert len(dets) == 2


class TestPostprocessNMS:
    """Test NMS + IoU."""

    def test_iou_full_overlap(self) -> None:
        """IoU box trùng hoàn toàn = 1."""
        assert ImagePostprocessor._iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0

    def test_iou_no_overlap(self) -> None:
        """IoU box tách rời = 0."""
        assert ImagePostprocessor._iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0

    def test_nms_removes_duplicates(self) -> None:
        """NMS giữ box conf cao, loại box trùng cùng class."""
        post = ImagePostprocessor(CLASS_MAP)
        raws = [
            RawDetection(0, 0.9, (0, 0, 10, 10)),
            RawDetection(0, 0.8, (1, 1, 11, 11)),  # trùng nhiều với box trên
        ]
        kept = post.nms(raws, iou_threshold=0.45)
        assert len(kept) == 1
        assert kept[0].confidence == 0.9

    def test_nms_keeps_different_class(self) -> None:
        """NMS class-aware — không loại box khác class."""
        post = ImagePostprocessor(CLASS_MAP)
        raws = [
            RawDetection(0, 0.9, (0, 0, 10, 10)),
            RawDetection(41, 0.8, (0, 0, 10, 10)),
        ]
        kept = post.nms(raws, iou_threshold=0.45)
        assert len(kept) == 2


class TestCoordinateMapping:
    """Test map tọa độ letterbox → gốc."""

    def test_map_coords_reverse_letterbox(self) -> None:
        """Bỏ padding + chia ratio để về ảnh gốc."""
        meta = LetterboxMeta(
            ratio=0.5, pad_w=10, pad_h=20, orig_w=640, orig_h=480, new_w=640, new_h=640
        )
        x1, y1, x2, y2 = ImagePostprocessor.map_coords_to_original(
            (10, 20, 110, 120), meta
        )
        # (10-10)/0.5=0 ; (20-20)/0.5=0 ; (110-10)/0.5=200 ; (120-20)/0.5=200
        assert (x1, y1, x2, y2) == (0.0, 0.0, 200.0, 200.0)

    def test_map_coords_clamped(self) -> None:
        """Tọa độ vượt biên bị clamp trong ảnh gốc."""
        meta = LetterboxMeta(
            ratio=1.0, pad_w=0, pad_h=0, orig_w=100, orig_h=100, new_w=640, new_h=640
        )
        _, _, x2, y2 = ImagePostprocessor.map_coords_to_original(
            (0, 0, 999, 999), meta
        )
        assert x2 == 100
        assert y2 == 100


class TestProcessBuildsDTO:
    """Test process trả Detection DTO đúng nhãn."""

    def test_process_builds_detection_with_label(self) -> None:
        """RawDetection → Detection có class_name logic."""
        post = ImagePostprocessor(CLASS_MAP)
        raws = [RawDetection(67, 0.9, (0, 0, 20, 40))]
        dets = post.process(raws)
        assert len(dets) == 1
        assert dets[0].class_name == "phone"
        assert dets[0].bbox.width == 20
