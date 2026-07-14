"""
Integration test — Camera → Detection → Tracking → Behavior Feature Engine.

KHÔNG cần torch/GPU: tracking chạy thuần numpy, pose dùng skeleton tổng hợp.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from app.modules.ai.models import BoundingBox, Detection, DetectionResult
from app.modules.behavior.config import BehaviorConfig
from app.modules.behavior.services import BehaviorService
from app.modules.tracking.config import TrackingConfig
from app.modules.tracking.services.tracking_service import TrackingService
from tests.modules.behavior.conftest import make_pose


def _detection(camera_id, frame_id, person_bbox, base_time):
    ts = base_time + timedelta(seconds=frame_id / 30.0)
    objects = [
        Detection("person", 0.95, BoundingBox(*person_bbox), 0),
        Detection("phone", 0.9, BoundingBox(115, 257, 135, 277), 67),
        Detection("monitor", 0.9, BoundingBox(300, 140, 360, 300), 62),
    ]
    return DetectionResult(
        camera_id=camera_id,
        frame_id=frame_id,
        timestamp=ts,
        objects=objects,
        width=1280,
        height=720,
    )


def test_pipeline_detection_tracking_behavior():
    tracking = TrackingService(TrackingConfig())
    behavior = BehaviorService(BehaviorConfig())  # pose không load → truyền poses
    base = datetime.now(timezone.utc)

    last_result = None
    for f in range(6):
        # người di chuyển nhẹ sang phải
        x1 = 100 + f * 2
        person_bbox = (x1, 140, x1 + 80, 360)
        det = _detection(1, f, person_bbox, base)
        tracking_result = tracking.process(det)

        # sinh pose tương ứng từng track
        poses = [make_pose(tuple(t.bbox)) for t in tracking_result.tracks]
        last_result = behavior.process(
            None, tracking_result, det.objects, poses=poses
        )

    assert last_result is not None
    assert last_result.count >= 1
    dto = last_result.features[0]
    assert dto.head.available
    assert dto.temporal_feature.motion_history >= 1
    # đặc trưng điện thoại (khoảng cách, không alert)
    assert dto.phone_feature.visible is True


def test_pipeline_live_and_track_api_state():
    tracking = TrackingService(TrackingConfig())
    behavior = BehaviorService(BehaviorConfig())
    base = datetime.now(timezone.utc)

    for f in range(4):
        det = _detection(1, f, (100, 140, 180, 360), base)
        tr = tracking.process(det)
        poses = [make_pose(tuple(t.bbox)) for t in tr.tracks]
        behavior.process(None, tr, det.objects, poses=poses)

    live = behavior.get_live()
    assert len(live) == 1
    stats = behavior.statistics()
    assert stats["frames_processed"] == 4
    assert stats["active_cameras"] == 1

    # track_id do tracking sinh, lấy từ kết quả camera
    cam_result = behavior.get_camera(1)
    assert cam_result is not None
    track_id = cam_result.features[0].track_id
    assert behavior.get_track(track_id) is not None


def test_visualizer_overlay_runs():
    import importlib.util

    if importlib.util.find_spec("cv2") is None:
        return  # bỏ qua nếu không có OpenCV

    from app.modules.behavior.utils.visualizer import draw_behavior

    tracking = TrackingService(TrackingConfig())
    behavior = BehaviorService(BehaviorConfig())
    det = _detection(1, 0, (100, 140, 180, 360), datetime.now(timezone.utc))
    tr = tracking.process(det)
    poses = [make_pose(tuple(t.bbox)) for t in tr.tracks]
    result = behavior.process(None, tr, det.objects, poses=poses)

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    out = draw_behavior(frame, tr, poses, result)
    assert out.shape == frame.shape
