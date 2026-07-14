"""VideoEvidenceManager — xuất video pre/post evidence time."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import numpy as np
from loguru import logger

from app.modules.event.config import RecorderConfig
from app.modules.event.evidence.frame_buffer import EvidenceFrameBuffer
from app.modules.event.exceptions import RecorderError
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import VideoRecord
from app.modules.event.utils.naming import build_evidence_name

_CODEC_FALLBACK = [("mp4v", ".mp4"), ("XVID", ".avi"), ("MJPG", ".avi")]


class VideoEvidenceManager:
    """Xuất MP4 10s trước + 10s sau evidence_time."""

    def __init__(self, config: RecorderConfig) -> None:
        self._config = config
        self._dir = Path(config.dir)
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover
            logger.warning("Không tạo được thư mục video: {}", exc)

    def export(
        self,
        event: BehaviorEventInput,
        buffer: EvidenceFrameBuffer,
        evidence_time: datetime,
        pre_seconds: Optional[float] = None,
        post_seconds: Optional[float] = None,
    ) -> Optional[VideoRecord]:
        if not self._config.enabled:
            return None
        pre = pre_seconds if pre_seconds is not None else self._config.pre_seconds
        post = post_seconds if post_seconds is not None else self._config.post_seconds
        frames = buffer.window(evidence_time, pre, post)
        if not frames:
            return VideoRecord(path="", status="no_frames", codec=self._config.codec)
        base = build_evidence_name(
            event.camera_id,
            event.camera_name,
            event.track_id,
            event.rule_id,
            evidence_time,
            "mp4",
        )
        start = time.perf_counter()
        try:
            path, codec = self._write(frames, base)
        except RecorderError as exc:
            logger.warning("Video evidence lỗi: {}", exc.message)
            return VideoRecord(path="", status="failed", codec=self._config.codec)
        elapsed = time.perf_counter() - start
        duration = len(frames) / float(self._config.fps or 1)
        if path is None:
            return VideoRecord(path="", status="skipped", codec=self._config.codec)
        logger.info(
            "Video evidence saved: {} ({} frames, {:.2f}s export)",
            path,
            len(frames),
            elapsed,
        )
        return VideoRecord(
            path=str(path), duration_s=duration, codec=codec, status="created"
        )

    def ready_at(self, evidence_time: datetime, post_seconds: Optional[float] = None) -> datetime:
        post = post_seconds if post_seconds is not None else self._config.post_seconds
        return evidence_time + timedelta(seconds=post)

    def _write(self, frames: List[np.ndarray], base: str) -> tuple[Optional[Path], str]:
        try:
            import cv2  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RecorderError(f"OpenCV không khả dụng: {exc}") from exc
        h, w = frames[0].shape[:2]
        for codec, ext in _CODEC_FALLBACK:
            out_path = self._dir / base.replace(".mp4", ext)
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(
                str(out_path), fourcc, float(self._config.fps), (w, h)
            )
            if not writer.isOpened():
                writer.release()
                continue
            try:
                for f in frames:
                    writer.write(self._prepare(f, w, h))
            except Exception as exc:  # pragma: no cover
                writer.release()
                raise RecorderError(f"Ghi video thất bại: {exc}") from exc
            writer.release()
            if out_path.exists() and out_path.stat().st_size > 0:
                return out_path, codec
        return None, self._config.codec

    @staticmethod
    def _prepare(frame: np.ndarray, w: int, h: int) -> np.ndarray:
        import cv2  # type: ignore

        f = frame
        if f.dtype != np.uint8:
            f = np.clip(f, 0, 255).astype(np.uint8)
        if f.ndim == 2:
            f = cv2.cvtColor(f, cv2.COLOR_GRAY2BGR)
        if f.shape[0] != h or f.shape[1] != w:
            f = cv2.resize(f, (w, h))
        return f
