"""
Auto Reconnect — exponential backoff 1s → 3s → 5s → 10s → 30s.

Không crash — worker loop tiếp tục sau mỗi lần thất bại.
"""

from typing import List


class ReconnectPolicy:
    """
    Chính sách thời gian chờ giữa các lần reconnect RTSP.

    Sau khi hết danh sách delays, lặp lại delay cuối cùng (30s).
    """

    def __init__(self, delays: List[int] | None = None) -> None:
        self._delays = delays or [1, 3, 5, 10, 30]
        self._attempt = 0

    @property
    def attempt(self) -> int:
        """Số lần reconnect đã thực hiện (tích lũy)."""
        return self._attempt

    def next_delay(self) -> float:
        """
        Trả về số giây chờ trước lần reconnect tiếp theo.

        Returns:
            float: Delay tính bằng giây.
        """
        idx = min(self._attempt, len(self._delays) - 1)
        delay = float(self._delays[idx])
        self._attempt += 1
        return delay

    def reset(self) -> None:
        """Reset counter sau khi kết nối thành công."""
        self._attempt = 0

    def record_success(self) -> None:
        """Alias reset — gọi khi connect OK."""
        self.reset()
