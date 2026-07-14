"""
VideoRecorder — xuất MP4 evidence từ ring buffer (pre + post event).

Dùng OpenCV VideoWriter (lazy import). Fallback codec + xử lý lỗi an toàn
(không raise ra pipeline; trả VideoRecord với status phù hợp).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

import numpy as np
from loguru import logger

from app.modules.event.config import RecorderConfig
from app.modules.event.exceptions import RecorderError
from app.modules.event.schemas.event import BehaviorEventInput
from app.modules.event.schemas.records import VideoRecord
from app.modules.event.utils.naming import build_evidence_name
from app.modules.event.video_recorder.ring_buffer import CameraRingBuffer

_CODEC_FALLBACK = [("mp4v", ".mp4"), ("XVID", ".avi"), ("MJPG", ".avi")]


class VideoRecorder:
    """Xuất video evidence từ ring buffer."""

    def __init__(self, config: RecorderConfig) -> None:
        self._config = config
        self._dir = Path(config.dir)
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover
            logger.warning("Không tạo được thư mục video: {}", exc)

    def record(
        self,
        event: BehaviorEventInput,
        buffer: Optional[CameraRingBuffer],
    ) -> Optional[VideoRecord]:
        """
        Xuất video evidence cho một event.

        Returns:
            VideoRecord (status: created/no_frames/skipped) hoặc None nếu tắt.
        """
        if not self._config.enabled:
            return None
        if buffer is None:
            return VideoRecord(path="", status="no_buffer", codec=self._config.codec)

        frames = buffer.window(
            event.start_time, self._config.pre_seconds, self._config.post_seconds
        )
        if not frames:
            return VideoRecord(path="", status="no_frames", codec=self._config.codec)

        base = build_evidence_name(
            event.camera_id, event.camera_name, event.track_id, event.rule_id,
            event.start_time, "mp4",
        )
        start = time.perf_counter()
        try:
            path, codec = self._write(frames, base)
        except RecorderError as exc:
            logger.warning("Recorder lỗi: {}", exc.message)
            return VideoRecord(path="", status="failed", codec=self._config.codec)

        elapsed = time.perf_counter() - start
        duration = len(frames) / float(self._config.fps or 1)
        if path is None:
            logger.warning("Không mở được VideoWriter cho {}", base)
            return VideoRecord(path="", status="skipped", codec=self._config.codec)

        logger.info("Video saved: {} ({} frames, {:.2f}s export)", path, len(frames), elapsed)
        return VideoRecord(
            path=str(path), duration_s=duration, codec=codec, status="created"
        )

    def _write(self, frames: List[np.ndarray], base: str) -> tuple[Optional[Path], str]:
        """Ghi frames ra file, thử lần lượt các codec."""
        try:
            import cv2  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RecorderError(f"OpenCV không khả dụng: {exc}") from exc

        h, w = frames[0].shape[:2]
        for codec, ext in _CODEC_FALLBACK:
            out_path = self._dir / base.replace(".mp4", ext)
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(str(out_path), fourcc, float(self._config.fps), (w, h))
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
        """Chuẩn hóa frame (kích thước + 3 kênh uint8)."""
        import cv2  # type: ignore

        f = frame
        if f.dtype != np.uint8:
            f = np.clip(f, 0, 255).astype(np.uint8)
        if f.ndim == 2:
            f = cv2.cvtColor(f, cv2.COLOR_GRAY2BGR)
        if f.shape[0] != h or f.shape[1] != w:
            f = cv2.resize(f, (w, h))
        return f
