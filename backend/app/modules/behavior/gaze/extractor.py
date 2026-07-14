"""
GazeFeatureExtractor — ƯỚC LƯỢNG hướng nhìn từ head feature + ngữ cảnh vật thể.

Lưu ý: chỉ là ước lượng, KHÔNG khẳng định tuyệt đối.
"""

from __future__ import annotations

from app.modules.behavior.models import GazeFeature, HeadFeature


class GazeFeatureExtractor:
    """Ước lượng Looking Monitor/Phone/Left/Right/Down."""

    def extract(
        self,
        head: HeadFeature,
        phone_near: bool,
        monitor_present: bool,
    ) -> GazeFeature:
        """
        Ước lượng hướng nhìn.

        Args:
            head: Đặc trưng đầu.
            phone_near: Tay/điện thoại gần nhau (từ phone feature).
            monitor_present: Có monitor trong khung.

        Returns:
            GazeFeature (looking + confidence ước lượng).
        """
        if not head.available:
            return GazeFeature(looking="UNKNOWN", confidence=0.0)

        direction = head.direction
        if direction == "DOWN" and phone_near:
            return GazeFeature(looking="PHONE", confidence=0.6)
        if direction == "FORWARD" and monitor_present:
            return GazeFeature(looking="MONITOR", confidence=0.5)
        if direction in ("LEFT", "RIGHT", "DOWN"):
            return GazeFeature(looking=direction, confidence=0.4)
        return GazeFeature(looking="FORWARD", confidence=0.3)
