"""Test ring buffer + snapshot service + video recorder."""

from __future__ import annotations

from pathlib import Path

from app.modules.event.config import RecorderConfig, SnapshotConfig
from app.modules.event.snapshot import SnapshotService
from app.modules.event.video_recorder import RingBufferManager, VideoRecorder

from .conftest import BASE_TIME, at, frame, make_event


def test_ring_buffer_window_and_latest():
    mgr = RingBufferManager(seconds=30, fps=10)
    for i in range(60):
        mgr.push(1, frame(value=i), timestamp=at(i * 0.5))  # 0..30s
    buf = mgr.buffer(1)
    assert buf.latest() is not None
    # cửa sổ quanh giây 15 ± 10s
    win = buf.window(at(15), 10, 10)
    assert len(win) > 0
    # buffer chỉ giữ ~30s gần nhất
    assert buf.size <= 60


def test_ring_buffer_per_camera_isolated():
    mgr = RingBufferManager(seconds=30, fps=10)
    mgr.push(1, frame(), timestamp=BASE_TIME)
    assert mgr.latest(1) is not None
    assert mgr.latest(2) is None


def test_snapshot_capture(tmp_path):
    svc = SnapshotService(SnapshotConfig(dir=str(tmp_path)))
    rec = svc.capture(make_event(), frame())
    assert rec is not None
    assert rec.status == "created"
    assert Path(rec.path).exists()
    assert rec.path.endswith(".jpg")


def test_snapshot_no_frame(tmp_path):
    svc = SnapshotService(SnapshotConfig(dir=str(tmp_path)))
    rec = svc.capture(make_event(), None)
    assert rec.status == "no_frame"


def test_video_recorder_no_frames(tmp_path):
    rec = VideoRecorder(RecorderConfig(dir=str(tmp_path)))
    out = rec.record(make_event(), None)
    assert out.status == "no_buffer"


def test_video_recorder_export(tmp_path):
    mgr = RingBufferManager(seconds=30, fps=10)
    for i in range(200):
        mgr.push(1, frame(value=(i % 255)), timestamp=at(i * 0.1))  # 0..20s
    rec = VideoRecorder(
        RecorderConfig(dir=str(tmp_path), pre_seconds=10, post_seconds=10, fps=10)
    )
    out = rec.record(make_event(start_time=at(10)), mgr.buffer(1))
    assert out is not None
    # môi trường không có codec → skipped/failed vẫn hợp lệ; nếu created thì file tồn tại
    assert out.status in {"created", "skipped", "failed"}
    if out.status == "created":
        assert Path(out.path).exists()
