"""
RTSPClient — kết nối và đọc frame qua OpenCV FFmpeg backend.

CHỈ đọc stream — không phân tích nội dung hình ảnh.
"""

import os
import time
from typing import Any, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from app.modules.camera.exceptions import RTSPConnectionError


class RTSPClient:
    """
    Wrapper OpenCV VideoCapture cho URL RTSP.

    Attributes:
        url: URL RTSP (main hoặc sub stream).
        timeout_seconds: Timeout mở stream.
    """

    def __init__(
        self,
        url: str,
        timeout_seconds: int = 10,
        frame_width: int = 0,
        frame_height: int = 0,
    ) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.frame_width = frame_width
        self.frame_height = frame_height
        self._cap: Optional[cv2.VideoCapture] = None

    @property
    def is_open(self) -> bool:
        """Stream có đang mở không."""
        return self._cap is not None and self._cap.isOpened()

    def connect(self) -> None:
        """
        Mở kết nối RTSP.

        Raises:
            RTSPConnectionError: Không mở được stream.
        """
        self.close()
        # Dahua / nhiều camera IP yêu cầu RTSP over TCP (đặc biệt trong Docker).
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
        logger.info("RTSP connecting | url={}", self._mask_url(self.url))
        cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if self.frame_width > 0:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        if self.frame_height > 0:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        deadline = time.monotonic() + self.timeout_seconds
        while not cap.isOpened() and time.monotonic() < deadline:
            time.sleep(0.1)

        if not cap.isOpened():
            cap.release()
            raise RTSPConnectionError(f"Không mở được RTSP: {self._mask_url(self.url)}")

        self._cap = cap
        logger.info("RTSP connected | url={}", self._mask_url(self.url))

    def read_frame(self) -> Tuple[Optional[np.ndarray], float, float]:
        """
        Đọc một frame từ stream.

        Returns:
            Tuple (frame BGR, read_time_ms, decode_time_ms).
            frame=None nếu đọc thất bại.
        """
        if not self.is_open or self._cap is None:
            return None, 0.0, 0.0

        t0 = time.perf_counter()
        ret, frame = self._cap.read()
        elapsed_ms = (time.perf_counter() - t0) * 1000

        if not ret or frame is None:
            logger.warning("Frame lost | url={}", self._mask_url(self.url))
            return None, elapsed_ms, elapsed_ms

        return frame, elapsed_ms, elapsed_ms

    def close(self) -> None:
        """Đóng stream và giải phóng tài nguyên."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("RTSP closed | url={}", self._mask_url(self.url))

    def reconnect(self) -> None:
        """Đóng và mở lại stream."""
        self.close()
        self.connect()

    @staticmethod
    def _mask_url(url: str) -> str:
        """Ẩn password trong URL khi log."""
        if "@" in url:
            prefix, rest = url.split("@", 1)
            if "://" in prefix:
                scheme, _ = prefix.split("://", 1)
                return f"{scheme}://***@{rest}"
        return url
