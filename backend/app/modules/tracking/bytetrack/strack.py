"""
STrack — một track đơn trong ByteTrack (bao Kalman state + vòng đời nội bộ).
"""

from __future__ import annotations

from typing import List

import numpy as np

from app.modules.tracking.bytetrack.kalman_filter import KalmanFilter


class InternalState:
    """Trạng thái nội bộ của ByteTrack (khác với TrackState nghiệp vụ)."""

    New = 0
    Tracked = 1
    Lost = 2
    Removed = 3


class STrack:
    """
    Track đơn dùng nội bộ ByteTrack.

    Giữ Kalman mean/covariance, track_id, score, class và vòng đời.
    """

    shared_kalman = KalmanFilter()

    def __init__(self, tlwh: np.ndarray, score: float, cls: int) -> None:
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter: KalmanFilter | None = None
        self.mean: np.ndarray | None = None
        self.covariance: np.ndarray | None = None
        self.is_activated = False
        self.score = float(score)
        self.cls = int(cls)
        self.track_id = 0
        self.state = InternalState.New
        self.frame_id = 0
        self.start_frame = 0
        self.tracklet_len = 0

    # ----- Vòng đời -----
    def mark_lost(self) -> None:
        """Đánh dấu track bị mất."""
        self.state = InternalState.Lost

    def mark_removed(self) -> None:
        """Đánh dấu track bị xóa."""
        self.state = InternalState.Removed

    @property
    def end_frame(self) -> int:
        """Frame cuối cùng track được cập nhật."""
        return self.frame_id

    def predict(self) -> None:
        """Dự đoán một bước Kalman."""
        mean_state = self.mean.copy()
        if self.state != InternalState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.shared_kalman.predict(
            mean_state, self.covariance
        )

    @staticmethod
    def multi_predict(stracks: List["STrack"]) -> None:
        """Dự đoán hàng loạt cho danh sách track."""
        for st in stracks:
            if st.mean is None:
                continue
            mean_state = st.mean.copy()
            if st.state != InternalState.Tracked:
                mean_state[7] = 0
            st.mean, st.covariance = STrack.shared_kalman.predict(
                mean_state, st.covariance
            )

    def activate(
        self, kalman_filter: KalmanFilter, frame_id: int, track_id: int
    ) -> None:
        """Kích hoạt track mới với track_id do tracker cấp (độc lập từng camera)."""
        self.kalman_filter = kalman_filter
        self.track_id = track_id
        self.mean, self.covariance = kalman_filter.initiate(
            self.tlwh_to_xyah(self._tlwh)
        )
        self.tracklet_len = 0
        self.state = InternalState.Tracked
        self.is_activated = frame_id == 1
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track: "STrack", frame_id: int) -> None:
        """Phục hồi track sau khi LOST (giữ nguyên track_id để ID ổn định)."""
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh)
        )
        self.tracklet_len = 0
        self.state = InternalState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        self.score = new_track.score
        self.cls = new_track.cls

    def update(self, new_track: "STrack", frame_id: int) -> None:
        """Cập nhật track đang theo dõi bằng detection mới."""
        self.frame_id = frame_id
        self.tracklet_len += 1
        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh)
        )
        self.state = InternalState.Tracked
        self.is_activated = True
        self.score = new_track.score
        self.cls = new_track.cls

    # ----- Chuyển đổi tọa độ -----
    @property
    def tlwh(self) -> np.ndarray:
        """(top-left x, y, width, height) hiện tại."""
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]  # a * h = w
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self) -> np.ndarray:
        """(x1, y1, x2, y2) hiện tại."""
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh: np.ndarray) -> np.ndarray:
        """(t,l,w,h) → (center_x, center_y, aspect, height)."""
        ret = np.asarray(tlwh, dtype=np.float32).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlbr_to_tlwh(tlbr: np.ndarray) -> np.ndarray:
        """(x1,y1,x2,y2) → (t,l,w,h)."""
        ret = np.asarray(tlbr, dtype=np.float32).copy()
        ret[2:] -= ret[:2]
        return ret
