"""
Integration test — Camera Service (Sprint 2) → Detection Engine (Sprint 3).

Mô phỏng: tạo FramePacket như Camera Service, đẩy qua DetectionPipeline
đa camera, verify DetectionResult + overlay bounding box.

KHÔNG lưu Database. KHÔNG gửi Telegram. Dùng FakeBackend (không cần GPU).
"""

import time

import numpy as np

from app.modules.ai.detection.pipeline import DetectionPipeline
from app.modules.ai.inference.engine import InferenceEngine
from app.modules.ai.inference.model_loader import ModelLoader
from app.modules.ai.models import RawDetection
from app.modules.ai.repositories.model_repository import ModelRepository
from app.modules.ai.utils.visualizer import draw_detections

# FramePacket của Camera Service Sprint 2 — chứng minh liên thông module
from app.modules.camera.models.frame import FramePacket, utc_now

from tests.modules.ai.conftest import FakeBackend


def _build_engine(config) -> InferenceEngine:
    """Engine dùng FakeBackend (person + cup)."""
    loader = ModelLoader(
        model_path=config.model.path,
        model_name=config.model.name,
        device="cpu",
        image_size=config.image_size,
        repository=ModelRepository(search_dirs=[]),
    )
    loader._backend = FakeBackend(
        [
            RawDetection(0, 0.92, (10, 10, 120, 300)),  # person
            RawDetection(41, 0.71, (200, 50, 260, 110)),  # cup
        ]
    )
    return InferenceEngine(loader, config)


class TestCameraToDetectionIntegration:
    """Camera frame → Detection → Overlay."""

    def test_frame_packet_flows_to_detection(self, detection_config) -> None:
        """FramePacket từ Camera Service được engine detect."""
        engine = _build_engine(detection_config)
        # Tạo FramePacket đúng như Camera Service Sprint 2 tạo ra
        packet = FramePacket(
            camera_id=1,
            frame_id=101,
            timestamp=utc_now(),
            data=np.zeros((360, 640, 3), dtype=np.uint8),
        )
        result = engine.infer(packet.data, packet.camera_id, packet.frame_id)
        assert result.camera_id == 1
        assert result.frame_id == 101
        labels = {o.class_name for o in result.objects}
        assert "person" in labels
        assert "cup" in labels

    def test_overlay_draw_produces_image(self, detection_config) -> None:
        """Overlay bounding box tạo ảnh cùng kích thước, không sửa gốc."""
        engine = _build_engine(detection_config)
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        result = engine.infer(frame, camera_id=1, frame_id=1)
        canvas = draw_detections(frame, result, camera_name="cam-1")
        assert canvas.shape == frame.shape
        # Overlay phải khác ảnh đen gốc (đã vẽ box/text)
        assert canvas.sum() > 0
        assert frame.sum() == 0  # ảnh gốc không bị sửa

    def test_multi_camera_pipeline_isolation(self, detection_config) -> None:
        """
        2 camera đẩy frame vào pipeline — mỗi camera có kết quả riêng.

        Chứng minh queue riêng, không camera nào block camera khác.
        """
        engine = _build_engine(detection_config)
        pipeline = DetectionPipeline(
            engine=engine,
            max_queue_size=3,
            num_workers=2,
            poll_interval_ms=2,
        )
        pipeline.register_camera(1)
        pipeline.register_camera(2)
        pipeline.start()
        try:
            for i in range(3):
                pipeline.submit(1, np.zeros((240, 320, 3), dtype=np.uint8), i)
                pipeline.submit(2, np.zeros((240, 320, 3), dtype=np.uint8), i)

            # Chờ worker xử lý
            deadline = time.time() + 5
            while time.time() < deadline:
                if (
                    pipeline.get_latest_result(1) is not None
                    and pipeline.get_latest_result(2) is not None
                ):
                    break
                time.sleep(0.05)

            r1 = pipeline.get_latest_result(1)
            r2 = pipeline.get_latest_result(2)
            assert r1 is not None and r1.camera_id == 1
            assert r2 is not None and r2.camera_id == 2
            assert pipeline.processed_count >= 2
        finally:
            pipeline.stop()

    def test_pipeline_drops_when_queue_full(self, detection_config) -> None:
        """Queue đầy → drop-oldest, không block (không deadlock)."""
        engine = _build_engine(detection_config)
        pipeline = DetectionPipeline(engine=engine, max_queue_size=2, num_workers=1)
        pipeline.register_camera(1)
        # Submit nhiều hơn queue khi worker chưa chạy → phải drop, không treo
        for i in range(10):
            pipeline.submit(1, np.zeros((100, 100, 3), dtype=np.uint8), i)
        q = pipeline._queues[1]
        assert q.size <= 2
        assert q.dropped_count >= 1
