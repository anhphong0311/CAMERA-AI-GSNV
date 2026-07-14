"""
HistoryManager — quản lý TemporalBuffer cho từng track (theo camera).

Giới hạn số track (chống Memory/Buffer Overflow) bằng cách loại LRU và
prune track không còn xuất hiện.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from loguru import logger

from app.modules.behavior.history.temporal_buffer import (
    FrameSnapshot,
    TemporalBuffer,
)


class HistoryManager:
    """Quản lý temporal buffer đa track cho MỘT camera."""

    def __init__(self, buffer_size: int = 300, max_tracks: int = 500) -> None:
        self._buffer_size = buffer_size
        self._max_tracks = max_tracks
        self._buffers: Dict[int, TemporalBuffer] = {}

    def get(self, track_id: int) -> Optional[TemporalBuffer]:
        """Buffer của track (hoặc None)."""
        return self._buffers.get(track_id)

    def get_or_create(self, track_id: int) -> TemporalBuffer:
        """Lấy hoặc tạo buffer; enforce sức chứa track."""
        buf = self._buffers.get(track_id)
        if buf is None:
            self._enforce_capacity()
            buf = TemporalBuffer(self._buffer_size)
            self._buffers[track_id] = buf
        return buf

    def update(
        self, track_id: int, snapshot: FrameSnapshot, frame_id: int
    ) -> TemporalBuffer:
        """Thêm snapshot cho track."""
        buf = self.get_or_create(track_id)
        buf.append(snapshot, frame_id)
        return buf

    def prune(self, current_frame_id: int) -> int:
        """
        Xóa buffer của track không xuất hiện quá buffer_size frame.

        Returns:
            Số buffer đã xóa.
        """
        stale = [
            tid
            for tid, buf in self._buffers.items()
            if current_frame_id - buf.last_frame_id > self._buffer_size
        ]
        for tid in stale:
            del self._buffers[tid]
        if stale:
            logger.debug("HistoryManager pruned {} stale buffers", len(stale))
        return len(stale)

    def _enforce_capacity(self) -> None:
        """Loại buffer ít được cập nhật nhất khi vượt max_tracks (LRU)."""
        while len(self._buffers) >= self._max_tracks:
            lru_id = min(
                self._buffers, key=lambda t: self._buffers[t].last_frame_id
            )
            del self._buffers[lru_id]
            logger.warning(
                "HistoryManager vượt max_tracks={} → loại track {}",
                self._max_tracks,
                lru_id,
            )

    @property
    def track_count(self) -> int:
        """Số track đang giữ buffer."""
        return len(self._buffers)

    def clear(self) -> None:
        """Xóa toàn bộ buffer."""
        self._buffers.clear()
