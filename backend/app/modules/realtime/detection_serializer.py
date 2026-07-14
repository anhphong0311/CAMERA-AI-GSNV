"""Chuyển DetectionResult (AI engine) → payload WebSocket cho Dashboard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.modules.ai.models import DetectionResult
from app.modules.behavior.models import BehaviorResult
from app.modules.behavior.utils.geometry import bbox_center, bbox_iou, distance

BBox = Tuple[float, float, float, float]


def _norm_bbox(x1: float, y1: float, x2: float, y2: float, w: int, h: int) -> list[float]:
    bw = max(0.0, x2 - x1)
    bh = max(0.0, y2 - y1)
    return [
        round(x1 / w, 4),
        round(y1 / h, 4),
        round(bw / w, 4),
        round(bh / h, 4),
    ]


def _match_track_id(bbox: BBox, tracks: Sequence) -> Optional[int]:
    best_id: Optional[int] = None
    best_iou = 0.0
    for track in tracks:
        iou = bbox_iou(bbox, track.bbox)
        if iou > best_iou:
            best_iou = iou
            best_id = track.track_id
    return best_id if best_iou >= 0.2 else None


def _phone_interaction_flags(
    behavior: Optional[BehaviorResult],
) -> tuple[bool, dict[int, bool]]:
    """Trả (có ai cầm điện thoại, map track_id → đang tương tác)."""
    by_track: dict[int, bool] = {}
    any_interaction = False
    if behavior is None:
        return False, by_track
    for feat in behavior.features:
        interacting = bool(feat.hand.near_phone)
        by_track[feat.track_id] = interacting
        any_interaction = any_interaction or interacting
    return any_interaction, by_track


def _phone_held_by_person(
    phone_xyxy: BBox,
    persons: Sequence,
    behavior: Optional[BehaviorResult],
    tracks: Sequence,
    width: int,
    height: int,
) -> tuple[bool, Optional[int]]:
    """
    Chỉ hiện phone khi gần tay người — loại súng quét mã / đồ trên bàn.
    """
    pc = bbox_center(phone_xyxy)
    hand_thresh = max(width, height) * 0.12

    if behavior is not None:
        for feat in behavior.features:
            if not feat.hand.near_phone:
                continue
            hand = feat.hand.left_position or feat.hand.right_position
            if hand is None:
                continue
            d = distance(hand, pc)
            if d is not None and d < hand_thresh:
                return True, feat.track_id

    for person in persons:
        pb = (
            person.bbox.x1,
            person.bbox.y1,
            person.bbox.x2,
            person.bbox.y2,
        )
        ph = pb[3] - pb[1]
        waist_y = pb[1] + ph * 0.55
        if pc[1] > waist_y + ph * 0.15:
            continue
        if bbox_iou(phone_xyxy, pb) > 0.005:
            tid = _match_track_id(pb, tracks)
            return True, tid
        if pb[0] <= pc[0] <= pb[2] and pb[1] <= pc[1] <= waist_y:
            if distance(pc, bbox_center(pb)) is not None:
                if distance(pc, bbox_center(pb)) < max(width, height) * 0.35:
                    return True, _match_track_id(pb, tracks)
    return False, None


def detection_result_to_dashboard(
    result: DetectionResult,
    *,
    tracking: Any = None,
    behavior: Optional[BehaviorResult] = None,
) -> Dict[str, Any]:
    """
    Map DTO detection sang schema Live Camera (bbox normalized 0..1).

    Khi có behavior: đánh dấu phone/person đang tương tác (tay gần điện thoại).
    """
    width = max(result.width, 1)
    height = max(result.height, 1)
    tracks = getattr(tracking, "tracks", []) if tracking is not None else []
    phone_active, track_phone = _phone_interaction_flags(behavior)
    persons = [o for o in result.objects if o.class_name == "person"]

    objects: List[Dict[str, Any]] = []
    for obj in result.objects:
        x1, y1, x2, y2 = obj.bbox.x1, obj.bbox.y1, obj.bbox.x2, obj.bbox.y2
        xyxy = (x1, y1, x2, y2)

        if obj.class_name == "phone":
            held, phone_track = _phone_held_by_person(
                xyxy, persons, behavior, tracks, width, height
            )
            if not held:
                continue
            track_id = phone_track
            interacting = phone_track is not None and track_phone.get(
                phone_track, False
            )
        else:
            track_id = _match_track_id(xyxy, tracks) if obj.class_name == "person" else None
            interacting = False
            if obj.class_name == "person" and track_id is not None:
                interacting = track_phone.get(track_id, False)

        entry: Dict[str, Any] = {
            "track_id": track_id,
            "label": obj.class_name,
            "confidence": round(float(obj.confidence), 4),
            "bbox": _norm_bbox(x1, y1, x2, y2, width, height),
        }
        if interacting:
            entry["interacting"] = True
        objects.append(entry)

    # Pose thấy tay gần phone nhưng YOLO chưa box phone — vẽ marker ảo
    if behavior is not None and phone_active:
        has_phone_box = any(o["label"] == "phone" for o in objects)
        if not has_phone_box:
            for feat in behavior.features:
                if not feat.hand.near_phone:
                    continue
                hand = feat.hand.left_position or feat.hand.right_position
                if hand is None:
                    continue
                hx, hy = hand
                size = max(width, height) * 0.04
                objects.append(
                    {
                        "track_id": feat.track_id,
                        "label": "phone",
                        "confidence": 0.5,
                        "bbox": _norm_bbox(
                            hx - size / 2,
                            hy - size / 2,
                            hx + size / 2,
                            hy + size / 2,
                            width,
                            height,
                        ),
                        "interacting": True,
                        "inferred": True,
                    }
                )
                break

    return {
        "camera_id": result.camera_id,
        "fps": round(result.fps, 1),
        "objects": objects,
        "ts": result.timestamp.isoformat(),
        "phone_interaction": phone_active,
    }
