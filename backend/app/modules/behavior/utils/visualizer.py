"""
Visualizer — overlay debug cho Behavior Engine (Skeleton, Joint, Head/Hand
Direction, Body Angle, Motion Vector). CHỈ dùng debug, không phần logic chính.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

from app.modules.behavior.models import BehaviorResult, PoseResult
from app.modules.behavior.models.keypoints import (
    LEFT_EAR,
    LEFT_EYE,
    NOSE,
    RIGHT_EAR,
    RIGHT_EYE,
    SKELETON_EDGES,
)
from app.modules.behavior.utils.geometry import midpoint

_JOINT_COLOR = (0, 255, 0)
_EDGE_COLOR = (255, 200, 0)
_HEAD_COLOR = (0, 128, 255)
_TEXT_COLOR = (255, 255, 255)


def draw_poses(frame: np.ndarray, poses: Sequence[PoseResult]) -> np.ndarray:
    """Vẽ skeleton, joint và mũi tên hướng đầu."""
    import cv2

    out = frame
    for pose in poses:
        kpts = pose.keypoints
        for a, b in SKELETON_EDGES:
            pa = kpts.get(a)
            pb = kpts.get(b)
            if pa and pb:
                cv2.line(
                    out,
                    (int(pa[0]), int(pa[1])),
                    (int(pb[0]), int(pb[1])),
                    _EDGE_COLOR,
                    2,
                )
        for j in range(len(kpts.points)):
            p = kpts.get(j)
            if p:
                cv2.circle(out, (int(p[0]), int(p[1])), 3, _JOINT_COLOR, -1)

        nose = kpts.get(NOSE)
        ear_mid = midpoint(kpts.get(LEFT_EAR), kpts.get(RIGHT_EAR)) or midpoint(
            kpts.get(LEFT_EYE), kpts.get(RIGHT_EYE)
        )
        if nose and ear_mid:
            dx = (nose[0] - ear_mid[0]) * 3
            dy = (nose[1] - ear_mid[1]) * 3
            cv2.arrowedLine(
                out,
                (int(nose[0]), int(nose[1])),
                (int(nose[0] + dx), int(nose[1] + dy)),
                _HEAD_COLOR,
                2,
                tipLength=0.3,
            )
    return out


def draw_behavior(
    frame: np.ndarray,
    tracking_result,
    poses: Sequence[PoseResult],
    behavior_result: Optional[BehaviorResult] = None,
) -> np.ndarray:
    """Vẽ skeleton + chú thích đặc trưng theo từng track."""
    import cv2

    out = draw_poses(frame, poses)
    feat_by_id = {}
    if behavior_result:
        feat_by_id = {f.track_id: f for f in behavior_result.features}

    for track in tracking_result.tracks:
        x1, y1, x2, y2 = (int(v) for v in track.bbox)
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 220, 220), 1)
        lines: List[str] = [f"ID {track.track_id}"]
        dto = feat_by_id.get(track.track_id)
        if dto:
            if dto.head.available:
                lines.append(f"head {dto.head.direction} {dto.head.angle:.0f}")
            if dto.body.available:
                lines.append(f"body {dto.body.lean}")
            if dto.hand.near_phone:
                lines.append(f"phone {dto.hand.distance_phone:.0f}")
            lines.append(f"gaze {dto.gaze.looking}")
            lines.append(f"sit {dto.chair_feature.sitting}")
            lines.append(f"stat {dto.motion.stationary_time:.1f}s")
        for i, text in enumerate(lines):
            cv2.putText(
                out,
                text,
                (x1 + 2, y1 + 14 + i * 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                _TEXT_COLOR,
                1,
                cv2.LINE_AA,
            )
    return out
