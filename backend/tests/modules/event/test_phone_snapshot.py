"""Tests — snapshot phone usage crop/annotate."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from app.modules.event.config import SnapshotConfig
from app.modules.event.evidence.snapshot_manager import SnapshotManager
from app.modules.event.schemas.event import BehaviorEventInput


def test_phone_usage_snapshot_crops_and_annotates(tmp_path):
    cfg = SnapshotConfig(enabled=True, dir=str(tmp_path), quality=85)
    mgr = SnapshotManager(cfg)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[:, :] = (40, 40, 40)
    # Fake person + phone region
    frame[200:500, 400:700] = (180, 180, 180)
    frame[320:380, 620:680] = (20, 20, 220)

    event = BehaviorEventInput(
        event_id="e1",
        camera_id=1,
        camera_name="CAM01",
        track_id=8,
        rule_id="PHONE_USAGE",
        event_type="PHONE_USAGE",
        severity="HIGH",
        confidence=0.9,
        start_time=datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc),
        duration=5.0,
        metadata={
            "person_bbox": [400, 200, 700, 500],
            "phone_bbox": [620, 320, 680, 380],
            "snapshot_hint": "phone_usage",
        },
    )
    composed = mgr._compose_phone_usage_frame(event, frame)
    assert composed.ndim == 3
    # Cropped around subject — smaller than full frame
    assert composed.shape[0] < frame.shape[0]
    assert composed.shape[1] < frame.shape[1]

    rec = mgr.capture(event, frame)
    assert rec is not None
    assert rec.status == "created"
    assert rec.path
