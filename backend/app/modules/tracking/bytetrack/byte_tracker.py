"""
BYTETracker — thuật toán ByteTrack (association 2 tầng theo confidence).

Tham chiếu: Zhang et al., "ByteTrack: Multi-Object Tracking by Associating
Every Detection Box" (2022). Cài đặt thuần numpy, độc lập từng camera.
"""

from __future__ import annotations

from typing import List

import numpy as np

from app.modules.tracking.bytetrack.kalman_filter import KalmanFilter
from app.modules.tracking.bytetrack.matching import (
    fuse_score,
    iou_distance,
    linear_assignment,
)
from app.modules.tracking.bytetrack.strack import InternalState, STrack
from app.modules.tracking.config import TrackerConfig


def joint_stracks(list_a: List[STrack], list_b: List[STrack]) -> List[STrack]:
    """Hợp 2 danh sách track theo track_id (không trùng)."""
    exists = {}
    res: List[STrack] = []
    for t in list_a:
        exists[t.track_id] = 1
        res.append(t)
    for t in list_b:
        if exists.get(t.track_id, 0) == 0:
            exists[t.track_id] = 1
            res.append(t)
    return res


def sub_stracks(list_a: List[STrack], list_b: List[STrack]) -> List[STrack]:
    """Hiệu list_a - list_b theo track_id."""
    stracks = {t.track_id: t for t in list_a}
    for t in list_b:
        stracks.pop(t.track_id, None)
    return list(stracks.values())


def remove_duplicate_stracks(
    stracks_a: List[STrack], stracks_b: List[STrack]
) -> tuple[List[STrack], List[STrack]]:
    """Loại track trùng lặp giữa 2 danh sách dựa trên IoU cao."""
    pdist = iou_distance(stracks_a, stracks_b)
    pairs = np.where(pdist < 0.15)
    dupa, dupb = [], []
    for p, q in zip(*pairs):
        timep = stracks_a[p].frame_id - stracks_a[p].start_frame
        timeq = stracks_b[q].frame_id - stracks_b[q].start_frame
        if timep > timeq:
            dupb.append(q)
        else:
            dupa.append(p)
    resa = [t for i, t in enumerate(stracks_a) if i not in dupa]
    resb = [t for i, t in enumerate(stracks_b) if i not in dupb]
    return resa, resb


class BYTETracker:
    """
    ByteTracker cho MỘT camera (id độc lập).

    update(dets, scores, classes) → danh sách STrack đang hoạt động.
    """

    def __init__(self, config: TrackerConfig) -> None:
        self._cfg = config
        self.frame_id = 0
        self.kalman_filter = KalmanFilter()
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []
        self.max_time_lost = int(config.frame_rate / 30.0 * config.track_buffer)
        self._id_count = 0

    def _next_id(self) -> int:
        """Cấp track_id tăng dần — độc lập cho camera này."""
        self._id_count += 1
        return self._id_count

    def update(
        self, dets: np.ndarray, scores: np.ndarray, classes: np.ndarray
    ) -> List[STrack]:
        """
        Cập nhật tracker với detection của một frame.

        Args:
            dets: (N,4) bbox tlbr.
            scores: (N,) confidence.
            classes: (N,) class id.

        Returns:
            Danh sách STrack đang hoạt động (is_activated).
        """
        self.frame_id += 1
        activated: List[STrack] = []
        refind: List[STrack] = []
        lost: List[STrack] = []
        removed: List[STrack] = []

        dets = np.asarray(dets, dtype=np.float32).reshape(-1, 4)
        scores = np.asarray(scores, dtype=np.float32).reshape(-1)
        classes = np.asarray(classes).reshape(-1)

        remain_inds = scores > self._cfg.track_thresh
        inds_low = scores > self._cfg.low_thresh
        inds_high = scores < self._cfg.track_thresh
        inds_second = np.logical_and(inds_low, inds_high)

        dets_high, scores_high, cls_high = (
            dets[remain_inds],
            scores[remain_inds],
            classes[remain_inds],
        )
        dets_second, scores_second, cls_second = (
            dets[inds_second],
            scores[inds_second],
            classes[inds_second],
        )

        detections = [
            STrack(STrack.tlbr_to_tlwh(t), s, c)
            for t, s, c in zip(dets_high, scores_high, cls_high)
        ]

        # Tách track chưa xác nhận vs đã theo dõi
        unconfirmed: List[STrack] = []
        tracked: List[STrack] = []
        for t in self.tracked_stracks:
            if not t.is_activated:
                unconfirmed.append(t)
            else:
                tracked.append(t)

        # ----- Stage 1: association với detection confidence cao -----
        strack_pool = joint_stracks(tracked, self.lost_stracks)
        STrack.multi_predict(strack_pool)
        dists = iou_distance(strack_pool, detections)
        dists = fuse_score(dists, detections)
        matches, u_track, u_det = linear_assignment(
            dists, thresh=self._cfg.match_thresh
        )
        for itr, idet in matches:
            track = strack_pool[itr]
            det = detections[idet]
            if track.state == InternalState.Tracked:
                track.update(det, self.frame_id)
                activated.append(track)
            else:
                track.re_activate(det, self.frame_id)
                refind.append(track)

        # ----- Stage 2: association với detection confidence thấp -----
        detections_second = [
            STrack(STrack.tlbr_to_tlwh(t), s, c)
            for t, s, c in zip(dets_second, scores_second, cls_second)
        ]
        r_tracked = [
            strack_pool[i]
            for i in u_track
            if strack_pool[i].state == InternalState.Tracked
        ]
        dists = iou_distance(r_tracked, detections_second)
        matches, u_track2, _ = linear_assignment(dists, thresh=0.5)
        for itr, idet in matches:
            track = r_tracked[itr]
            det = detections_second[idet]
            if track.state == InternalState.Tracked:
                track.update(det, self.frame_id)
                activated.append(track)
            else:
                track.re_activate(det, self.frame_id)
                refind.append(track)

        for it in u_track2:
            track = r_tracked[it]
            if track.state != InternalState.Lost:
                track.mark_lost()
                lost.append(track)

        # ----- Track chưa xác nhận -----
        detections = [detections[i] for i in u_det]
        dists = iou_distance(unconfirmed, detections)
        dists = fuse_score(dists, detections)
        matches, u_unconfirmed, u_det = linear_assignment(dists, thresh=0.7)
        for itr, idet in matches:
            unconfirmed[itr].update(detections[idet], self.frame_id)
            activated.append(unconfirmed[itr])
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed.append(track)

        # ----- Khởi tạo track mới -----
        for inew in u_det:
            track = detections[inew]
            if track.score < self._cfg.new_track_thresh:
                continue
            track.activate(self.kalman_filter, self.frame_id, self._next_id())
            activated.append(track)

        # ----- Hết hạn track LOST → REMOVED -----
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed.append(track)

        # ----- Gộp lại -----
        self.tracked_stracks = [
            t for t in self.tracked_stracks if t.state == InternalState.Tracked
        ]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(
            self.tracked_stracks, self.lost_stracks
        )
        # Chống tràn bộ nhớ: chỉ giữ removed gần đây
        if len(self.removed_stracks) > 1000:
            self.removed_stracks = self.removed_stracks[-1000:]

        return [t for t in self.tracked_stracks if t.is_activated]
