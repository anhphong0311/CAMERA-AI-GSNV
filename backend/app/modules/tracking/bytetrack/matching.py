"""
Matching cho ByteTrack — IoU distance + linear assignment (Hungarian thuần numpy).

Cài đặt bài toán gán (assignment problem) bằng thuật toán Hungarian O(n^3)
theo phương pháp đường tăng ngắn nhất (không cần scipy/lap).
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np


def _hungarian_min(cost: np.ndarray) -> np.ndarray:
    """
    Giải bài toán gán cực tiểu cho ma trận cost (n hàng ≤ m cột).

    Trả về mảng col[i] = cột được gán cho hàng i (đảm bảo n <= m).

    Thuật toán Hungarian (Kuhn-Munkres) dạng đường tăng ngắn nhất, 1-indexed.
    """
    n, m = cost.shape
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)  # p[j] = hàng gán cho cột j
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1, j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(0, m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    col_for_row = np.full(n, -1, dtype=int)
    for j in range(1, m + 1):
        if p[j] != 0:
            col_for_row[p[j] - 1] = j - 1
    return col_for_row


def linear_assignment(
    cost_matrix: np.ndarray, thresh: float
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Gán tối ưu theo cost, chỉ giữ cặp có cost <= thresh.

    Args:
        cost_matrix: Ma trận cost (rows=tracks, cols=detections).
        thresh: Ngưỡng cost tối đa để chấp nhận cặp.

    Returns:
        (matches, unmatched_rows, unmatched_cols).
    """
    if cost_matrix.size == 0:
        return (
            [],
            list(range(cost_matrix.shape[0])),
            list(range(cost_matrix.shape[1])),
        )

    rows, cols = cost_matrix.shape
    if rows <= cols:
        assign = _hungarian_min(cost_matrix)
        pairs = [(r, int(assign[r])) for r in range(rows) if assign[r] != -1]
    else:
        assign_t = _hungarian_min(cost_matrix.T)
        pairs = [(int(assign_t[c]), c) for c in range(cols) if assign_t[c] != -1]

    matches: List[Tuple[int, int]] = []
    for r, c in pairs:
        if cost_matrix[r, c] <= thresh:
            matches.append((r, c))

    matched_rows = {r for r, _ in matches}
    matched_cols = {c for _, c in matches}
    unmatched_rows = [r for r in range(rows) if r not in matched_rows]
    unmatched_cols = [c for c in range(cols) if c not in matched_cols]
    return matches, unmatched_rows, unmatched_cols


def bbox_ious(atlbrs: np.ndarray, btlbrs: np.ndarray) -> np.ndarray:
    """
    Tính ma trận IoU giữa 2 tập box tlbr.

    Args:
        atlbrs: (N,4), btlbrs: (M,4).

    Returns:
        (N,M) IoU.
    """
    if atlbrs.size == 0 or btlbrs.size == 0:
        return np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)

    area_a = (atlbrs[:, 2] - atlbrs[:, 0]) * (atlbrs[:, 3] - atlbrs[:, 1])
    area_b = (btlbrs[:, 2] - btlbrs[:, 0]) * (btlbrs[:, 3] - btlbrs[:, 1])

    lt = np.maximum(atlbrs[:, None, :2], btlbrs[None, :, :2])
    rb = np.minimum(atlbrs[:, None, 2:], btlbrs[None, :, 2:])
    wh = np.clip(rb - lt, a_min=0, a_max=None)
    inter = wh[:, :, 0] * wh[:, :, 1]
    union = area_a[:, None] + area_b[None, :] - inter
    return np.where(union > 0, inter / union, 0.0).astype(np.float32)


def iou_distance(atracks: Sequence, btracks: Sequence) -> np.ndarray:
    """
    Cost = 1 - IoU giữa các track (dùng tlbr dự đoán) và detection.

    Args:
        atracks, btracks: Danh sách đối tượng có thuộc tính `.tlbr`.

    Returns:
        Ma trận cost (len(a), len(b)).
    """
    atlbrs = np.array([t.tlbr for t in atracks], dtype=np.float32).reshape(-1, 4)
    btlbrs = np.array([t.tlbr for t in btracks], dtype=np.float32).reshape(-1, 4)
    ious = bbox_ious(atlbrs, btlbrs)
    return 1.0 - ious


def fuse_score(cost_matrix: np.ndarray, detections: Sequence) -> np.ndarray:
    """
    Kết hợp IoU similarity với detection score (giảm ID switch).

    Args:
        cost_matrix: Cost = 1 - IoU.
        detections: Danh sách detection có `.score`.

    Returns:
        Cost đã fuse.
    """
    if cost_matrix.size == 0:
        return cost_matrix
    iou_sim = 1.0 - cost_matrix
    det_scores = np.array([d.score for d in detections])
    det_scores = np.expand_dims(det_scores, axis=0).repeat(cost_matrix.shape[0], axis=0)
    fuse_sim = iou_sim * det_scores
    return 1.0 - fuse_sim
