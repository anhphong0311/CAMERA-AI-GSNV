"""SnapshotManager — chụp snapshot tại thời điểm evidence chính xác."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from loguru import logger

from app.modules.event.config import SnapshotConfig
from app.modules.event.evidence.frame_buffer import EvidenceFrameBuffer
from app.modules.event.exceptions import SnapshotError
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import SnapshotRecord
from app.modules.event.utils.naming import build_evidence_name

BBox = Tuple[float, float, float, float]


class SnapshotManager:
    """Lưu JPG tại evidence_time — không chụp lúc gửi Telegram."""

    def __init__(self, config: SnapshotConfig) -> None:
        self._config = config
        self._dir = Path(config.dir)
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover
            logger.warning("Không tạo được thư mục snapshot: {}", exc)

    def capture_at(
        self,
        event: BehaviorEventInput,
        buffer: EvidenceFrameBuffer,
        evidence_time: datetime,
    ) -> Optional[SnapshotRecord]:
        if not self._config.enabled:
            return None
        # AWAY / PHONE: ưu tiên frame mới nhất lúc cảnh báo
        if event.rule_id in ("AWAY_FROM_DESK", "PHONE_USAGE"):
            frame = buffer.latest()
            if frame is None:
                frame = buffer.get_snapshot(evidence_time)
        else:
            frame = buffer.get_snapshot(evidence_time)
            if frame is None:
                frame = buffer.latest()
        if frame is None:
            return SnapshotRecord(path="", status="no_frame")

        if event.rule_id == "PHONE_USAGE":
            frame = self._compose_phone_usage_frame(event, frame)

        return self._write(event, frame, evidence_time)

    def capture(
        self, event: BehaviorEventInput, frame: Optional[np.ndarray]
    ) -> Optional[SnapshotRecord]:
        """Fallback khi có frame sẵn."""
        if not self._config.enabled:
            return None
        if frame is None:
            return SnapshotRecord(path="", status="no_frame")
        if event.rule_id == "PHONE_USAGE":
            frame = self._compose_phone_usage_frame(event, frame)
        return self._write(event, frame, event.evidence_time or event.start_time)

    def _compose_phone_usage_frame(
        self, event: BehaviorEventInput, frame: np.ndarray
    ) -> np.ndarray:
        """Crop gần nhân viên + vẽ khung person/phone để thấy rõ đang dùng máy."""
        meta = event.metadata or {}
        person = self._as_bbox(meta.get("person_bbox"))
        phone = self._as_bbox(meta.get("phone_bbox"))
        annotated = self._annotate_phone_usage(frame, person, phone, event.track_id)
        cropped = self._crop_subject(annotated, person, phone)
        return cropped if cropped is not None else annotated

    @staticmethod
    def _as_bbox(raw) -> Optional[BBox]:
        if raw is None:
            return None
        try:
            vals = [float(v) for v in raw]
            if len(vals) != 4:
                return None
            return vals[0], vals[1], vals[2], vals[3]
        except (TypeError, ValueError):
            return None

    def _annotate_phone_usage(
        self,
        frame: np.ndarray,
        person: Optional[BBox],
        phone: Optional[BBox],
        track_id: int,
    ) -> np.ndarray:
        try:
            import cv2  # type: ignore
        except ImportError:  # pragma: no cover
            return frame

        out = frame.copy()
        if out.dtype != np.uint8:
            out = np.clip(out, 0, 255).astype(np.uint8)

        if person is not None:
            x1, y1, x2, y2 = (int(v) for v in person)
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 220, 0), 3)
            cv2.putText(
                out,
                f"NV #{track_id}",
                (x1, max(24, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 220, 0),
                2,
                cv2.LINE_AA,
            )

        if phone is not None:
            x1, y1, x2, y2 = (int(v) for v in phone)
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(
                out,
                "DIEN THOAI",
                (x1, max(24, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        cv2.putText(
            out,
            "SU DUNG DIEN THOAI",
            (16, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        return out

    def _crop_subject(
        self,
        frame: np.ndarray,
        person: Optional[BBox],
        phone: Optional[BBox],
        padding_ratio: float = 0.35,
        min_side: int = 320,
    ) -> Optional[np.ndarray]:
        """Cắt vùng quanh người (+ phone) để ảnh Telegram nhìn rõ nhân viên."""
        boxes = [b for b in (person, phone) if b is not None]
        if not boxes:
            return None
        h, w = frame.shape[:2]
        x1 = min(b[0] for b in boxes)
        y1 = min(b[1] for b in boxes)
        x2 = max(b[2] for b in boxes)
        y2 = max(b[3] for b in boxes)
        bw, bh = max(x2 - x1, 1.0), max(y2 - y1, 1.0)
        pad_x = bw * padding_ratio
        pad_y = bh * padding_ratio
        # Đảm bảo vùng crop đủ lớn để nhìn rõ
        side = max(bw + 2 * pad_x, bh + 2 * pad_y, float(min_side))
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        half = side / 2.0
        left = int(max(0, cx - half))
        top = int(max(0, cy - half))
        right = int(min(w, cx + half))
        bottom = int(min(h, cy + half))
        if right - left < 64 or bottom - top < 64:
            return None
        return frame[top:bottom, left:right].copy()

    def _write(
        self, event: BehaviorEventInput, frame: np.ndarray, at: datetime
    ) -> SnapshotRecord:
        name = build_evidence_name(
            event.camera_id,
            event.camera_name,
            event.track_id,
            event.rule_id,
            at,
            self._config.format,
        )
        out_path = self._dir / name
        start = time.perf_counter()
        try:
            h, w = self._write_jpg(frame, out_path)
        except SnapshotError as exc:
            logger.warning("Snapshot lỗi: {}", exc.message)
            return SnapshotRecord(path="", status="failed")
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.info("Snapshot at {} saved: {} ({:.0f}ms)", at.isoformat(), out_path, elapsed_ms)
        return SnapshotRecord(path=str(out_path), width=w, height=h, status="created")

    def _write_jpg(self, frame: np.ndarray, out_path: Path) -> tuple[int, int]:
        try:
            import cv2  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise SnapshotError(f"OpenCV không khả dụng: {exc}") from exc
        f = frame
        if f.dtype != np.uint8:
            f = np.clip(f, 0, 255).astype(np.uint8)
        h, w = f.shape[:2]
        params = [int(cv2.IMWRITE_JPEG_QUALITY), int(self._config.quality)]
        ok = cv2.imwrite(str(out_path), f, params)
        if not ok or not out_path.exists():
            raise SnapshotError(f"Không ghi được snapshot: {out_path}")
        return w, h
