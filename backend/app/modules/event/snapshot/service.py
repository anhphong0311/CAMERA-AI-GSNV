"""
SnapshotService — lưu JPG bằng chứng từ frame gần nhất khi event xác nhận.

Đặt tên theo Camera / Track / Rule / Timestamp. Yêu cầu < 200ms.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger

from app.modules.event.config import SnapshotConfig
from app.modules.event.exceptions import SnapshotError
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import SnapshotRecord
from app.modules.event.utils.naming import build_evidence_name


class SnapshotService:
    """Tạo snapshot evidence."""

    def __init__(self, config: SnapshotConfig) -> None:
        self._config = config
        self._dir = Path(config.dir)
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover
            logger.warning("Không tạo được thư mục snapshot: {}", exc)

    def capture(
        self, event: BehaviorEventInput, frame: Optional[np.ndarray]
    ) -> Optional[SnapshotRecord]:
        """
        Lưu snapshot JPG cho một event.

        Returns:
            SnapshotRecord (status created/no_frame) hoặc None nếu tắt.
        """
        if not self._config.enabled:
            return None
        if frame is None:
            return SnapshotRecord(path="", status="no_frame")

        name = build_evidence_name(
            event.camera_id, event.camera_name, event.track_id, event.rule_id,
            event.start_time, self._config.format,
        )
        out_path = self._dir / name
        start = time.perf_counter()
        try:
            h, w = self._write(frame, out_path)
        except SnapshotError as exc:
            logger.warning("Snapshot lỗi: {}", exc.message)
            return SnapshotRecord(path="", status="failed")

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if elapsed_ms > self._config.timeout_ms:
            logger.warning(
                "Snapshot chậm {:.0f}ms > {}ms", elapsed_ms, self._config.timeout_ms
            )
        logger.info("Snapshot saved: {} ({:.0f}ms)", out_path, elapsed_ms)
        return SnapshotRecord(path=str(out_path), width=w, height=h, status="created")

    def _write(self, frame: np.ndarray, out_path: Path) -> tuple[int, int]:
        """Ghi JPG; trả (w, h)."""
        try:
            import cv2  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise SnapshotError(f"OpenCV không khả dụng: {exc}") from exc

        f = frame
        if f.dtype != np.uint8:
            f = np.clip(f, 0, 255).astype(np.uint8)
        h, w = f.shape[:2]
        params = [int(cv2.IMWRITE_JPEG_QUALITY), int(self._config.quality)]
        try:
            ok = cv2.imwrite(str(out_path), f, params)
        except Exception as exc:  # pragma: no cover
            raise SnapshotError(f"imwrite lỗi: {exc}") from exc
        if not ok or not out_path.exists():
            raise SnapshotError(f"Không ghi được snapshot: {out_path}")
        return w, h
