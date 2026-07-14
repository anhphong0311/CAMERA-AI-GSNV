"""
Unit tests — DTO DetectionResult / BoundingBox / Detection.
"""

from datetime import datetime, timezone

from app.modules.ai.models import BoundingBox, Detection, DetectionResult


class TestBoundingBox:
    """Test hình học bounding box."""

    def test_width_height_center(self) -> None:
        """Tính width/height/center đúng."""
        box = BoundingBox(10, 20, 110, 220)
        assert box.width == 100
        assert box.height == 200
        assert box.center == (60, 120)
        assert box.area == 100 * 200

    def test_to_dict(self) -> None:
        """Serialize bbox."""
        box = BoundingBox(1.234, 2.0, 3.0, 4.0)
        d = box.to_dict()
        assert d["x1"] == 1.23


class TestDetection:
    """Test Detection DTO."""

    def test_to_dict_schema(self) -> None:
        """DTO có đủ class/confidence/bbox/center/width/height."""
        det = Detection("person", 0.912345, BoundingBox(0, 0, 50, 100), class_id=0)
        d = det.to_dict()
        assert d["class"] == "person"
        assert d["confidence"] == 0.9123
        assert d["width"] == 50
        assert d["height"] == 100
        assert d["center"] == {"x": 25.0, "y": 50.0}


class TestDetectionResult:
    """Test DetectionResult DTO."""

    def test_fps_from_inference_time(self) -> None:
        """FPS suy từ inference_time_ms."""
        result = DetectionResult(
            camera_id=1,
            frame_id=5,
            timestamp=datetime.now(timezone.utc),
            inference_time_ms=20.0,
        )
        assert result.fps == 50.0
        assert result.count == 0

    def test_to_dict_full(self) -> None:
        """Serialize DetectionResult chuẩn JSON."""
        det = Detection("phone", 0.8, BoundingBox(0, 0, 10, 10), class_id=67)
        result = DetectionResult(
            camera_id=2,
            frame_id=7,
            timestamp=datetime.now(timezone.utc),
            objects=[det],
            inference_time_ms=25.0,
            model_name="yolo11n",
            width=640,
            height=480,
        )
        d = result.to_dict()
        assert d["camera_id"] == 2
        assert d["count"] == 1
        assert d["objects"][0]["class"] == "phone"
        assert d["model_name"] == "yolo11n"
        assert d["fps"] == 40.0

    def test_zero_inference_time_fps_zero(self) -> None:
        """inference_time=0 → fps=0 (không chia 0)."""
        result = DetectionResult(
            camera_id=1, frame_id=1, timestamp=datetime.now(timezone.utc)
        )
        assert result.fps == 0.0
