"""
Unit tests — RTSPClient với mock OpenCV.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.modules.camera.exceptions import RTSPConnectionError
from app.modules.camera.stream_reader.rtsp_client import RTSPClient


class TestRTSPClient:
    """Test RTSPClient không cần camera thật."""

    @patch("app.modules.camera.stream_reader.rtsp_client.cv2.VideoCapture")
    def test_connect_success(self, mock_vc: MagicMock) -> None:
        """Connect thành công khi cap.isOpened()=True."""
        cap = MagicMock()
        cap.isOpened.return_value = True
        mock_vc.return_value = cap

        client = RTSPClient("rtsp://test/stream", timeout_seconds=1)
        client.connect()
        assert client.is_open

    @patch("app.modules.camera.stream_reader.rtsp_client.cv2.VideoCapture")
    def test_connect_failure_raises(self, mock_vc: MagicMock) -> None:
        """Connect thất bại — raise RTSPConnectionError."""
        cap = MagicMock()
        cap.isOpened.return_value = False
        mock_vc.return_value = cap

        client = RTSPClient("rtsp://bad/stream", timeout_seconds=1)
        with pytest.raises(RTSPConnectionError):
            client.connect()

    @patch("app.modules.camera.stream_reader.rtsp_client.cv2.VideoCapture")
    def test_read_frame_success(self, mock_vc: MagicMock) -> None:
        """read_frame trả numpy array."""
        cap = MagicMock()
        cap.isOpened.return_value = True
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cap.read.return_value = (True, frame)
        mock_vc.return_value = cap

        client = RTSPClient("rtsp://test/stream")
        client.connect()
        data, read_ms, dec_ms = client.read_frame()
        assert data is not None
        assert data.shape == (480, 640, 3)
        assert read_ms >= 0

    @patch("app.modules.camera.stream_reader.rtsp_client.cv2.VideoCapture")
    def test_read_frame_failure_returns_none(self, mock_vc: MagicMock) -> None:
        """read_frame thất bại — trả None."""
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.read.return_value = (False, None)
        mock_vc.return_value = cap

        client = RTSPClient("rtsp://test/stream")
        client.connect()
        data, _, _ = client.read_frame()
        assert data is None

    @patch("app.modules.camera.stream_reader.rtsp_client.cv2.VideoCapture")
    def test_close_releases_capture(self, mock_vc: MagicMock) -> None:
        """close() gọi release."""
        cap = MagicMock()
        cap.isOpened.return_value = True
        mock_vc.return_value = cap

        client = RTSPClient("rtsp://test/stream")
        client.connect()
        client.close()
        cap.release.assert_called_once()
        assert not client.is_open
