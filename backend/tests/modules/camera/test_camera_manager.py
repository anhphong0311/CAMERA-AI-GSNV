"""
Unit tests — CameraManager multi-camera isolation.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.modules.camera.camera_manager.manager import CameraManager
from app.modules.camera.exceptions import CameraAlreadyRunningError, CameraNotRunningError
from app.modules.camera.utils.config_loader import CameraStreamConfig


class TestCameraManager:
    """Test CameraManager với mock worker."""

    def setup_method(self) -> None:
        """Fresh manager mỗi test."""
        self.config = CameraStreamConfig(
            queue_size=5, target_fps=10, reconnect_delays=[1]
        )
        self.manager = CameraManager(config=self.config)

    def test_register_and_list(self) -> None:
        """Register URL không start worker."""
        self.manager.register_camera(1, "rtsp://cam1")
        assert 1 not in self.manager.list_running_ids()

    @patch("app.modules.camera.camera_manager.manager.CameraWorker")
    def test_start_stop_camera(self, mock_worker_cls: MagicMock) -> None:
        """Start và stop worker."""
        worker = MagicMock()
        worker.is_running = True
        mock_worker_cls.return_value = worker

        self.manager.register_camera(1, "rtsp://cam1")
        self.manager.start_camera(1)
        worker.start.assert_called_once()
        assert 1 in self.manager.list_running_ids()

        worker.is_running = False
        self.manager.stop_camera(1)
        worker.stop.assert_called_once()

    @patch("app.modules.camera.camera_manager.manager.CameraWorker")
    def test_start_twice_raises_conflict(self, mock_worker_cls: MagicMock) -> None:
        """Start camera đang chạy — CameraAlreadyRunningError."""
        worker = MagicMock()
        worker.is_running = True
        mock_worker_cls.return_value = worker

        self.manager.register_camera(1, "rtsp://cam1")
        self.manager.start_camera(1)
        with pytest.raises(CameraAlreadyRunningError):
            self.manager.start_camera(1)

    def test_stop_not_running_raises(self) -> None:
        """Stop camera chưa chạy."""
        with pytest.raises(CameraNotRunningError):
            self.manager.stop_camera(99)

    @patch("app.modules.camera.camera_manager.manager.CameraWorker")
    def test_one_camera_failure_does_not_affect_other(self, mock_worker_cls: MagicMock) -> None:
        """Bulkhead — 2 camera độc lập."""
        workers = {}

        def make_worker(**kwargs):
            w = MagicMock()
            w.is_running = True
            cid = kwargs.get("camera_id", 0)
            workers[cid] = w
            return w

        mock_worker_cls.side_effect = make_worker

        self.manager.register_camera(1, "rtsp://cam1")
        self.manager.register_camera(2, "rtsp://cam2")
        self.manager.start_camera(1)
        self.manager.start_camera(2)

        workers[1].is_running = False
        self.manager.stop_camera(1)
        assert 2 in self.manager.list_running_ids()

    @patch("app.modules.camera.camera_manager.manager.CameraWorker")
    def test_stop_all(self, mock_worker_cls: MagicMock) -> None:
        """stop_all dừng mọi worker."""
        worker = MagicMock()
        worker.is_running = True
        mock_worker_cls.return_value = worker

        self.manager.register_camera(1, "rtsp://cam1")
        self.manager.start_camera(1)
        self.manager.stop_all()
        assert self.manager.list_running_ids() == []
