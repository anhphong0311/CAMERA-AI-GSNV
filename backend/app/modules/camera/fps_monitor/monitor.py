"""
FPS Monitor — đo FPS, read/decode time, queue size.
"""

import threading
import time
from collections import deque
from typing import Deque


class FPSMonitor:
    """
    Theo dõi FPS rolling window và timing đọc frame.

    Thread-safe qua Lock.
    """

    def __init__(self, window_size: int = 30) -> None:
        self._timestamps: Deque[float] = deque(maxlen=window_size)
        self._read_times: Deque[float] = deque(maxlen=window_size)
        self._decode_times: Deque[float] = deque(maxlen=window_size)
        self._lock = threading.RLock()
        self._total_frames: int = 0
        self._session_start: float = time.monotonic()

    def record_frame(
        self,
        read_time_ms: float = 0.0,
        decode_time_ms: float = 0.0,
    ) -> None:
        """
        Ghi nhận một frame mới.

        Args:
            read_time_ms: Thời gian read từ stream.
            decode_time_ms: Thời gian decode (thường gộp trong read với OpenCV).
        """
        now = time.monotonic()
        with self._lock:
            self._timestamps.append(now)
            self._read_times.append(read_time_ms)
            self._decode_times.append(decode_time_ms)
            self._total_frames += 1

    @property
    def current_fps(self) -> float:
        """
        FPS tính từ các frame trong rolling window.

        Returns:
            float: FPS hiện tại.
        """
        with self._lock:
            if len(self._timestamps) < 2:
                return 0.0
            elapsed = self._timestamps[-1] - self._timestamps[0]
            if elapsed <= 0:
                return 0.0
            return (len(self._timestamps) - 1) / elapsed

    @property
    def average_fps(self) -> float:
        """
        FPS trung bình từ lúc worker start.

        Returns:
            float: Average FPS.
        """
        with self._lock:
            elapsed = time.monotonic() - self._session_start
            if elapsed <= 0 or self._total_frames == 0:
                return 0.0
            return self._total_frames / elapsed

    @property
    def avg_read_time_ms(self) -> float:
        """Thời gian đọc trung bình (ms)."""
        with self._lock:
            if not self._read_times:
                return 0.0
            return sum(self._read_times) / len(self._read_times)

    @property
    def avg_decode_time_ms(self) -> float:
        """Thời gian decode trung bình (ms)."""
        with self._lock:
            if not self._decode_times:
                return 0.0
            return sum(self._decode_times) / len(self._decode_times)

    def reset(self) -> None:
        """Reset metrics khi restart worker."""
        with self._lock:
            self._timestamps.clear()
            self._read_times.clear()
            self._decode_times.clear()
            self._total_frames = 0
            self._session_start = time.monotonic()
