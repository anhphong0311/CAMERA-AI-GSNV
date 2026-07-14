"""
FactExtractor — gộp dữ liệu Detection/Tracking/Behavior thành dict "facts".

Rule tham chiếu fact theo tên. Đây là điểm DUY NHẤT map dữ liệu → fact,
giúp rule không phụ thuộc cấu trúc DTO nội bộ (duck-typed, không import cứng).
"""

from __future__ import annotations

from typing import Any, Optional


def _looking(dto: Any) -> str:
    gaze = getattr(dto, "gaze", None)
    return getattr(gaze, "looking", "UNKNOWN") if gaze else "UNKNOWN"


def build_facts(
    dto: Any,
    track: Any,
    person_count: int,
    nearest_distance: Optional[float],
    low_motion_speed: float,
    nearby_distance: float,
    *,
    desk_roi_configured: bool = False,
) -> dict[str, Any]:
    """
    Dựng dict facts cho một track.

    Args:
        dto: BehaviorFeatureDTO (Sprint 5).
        track: Track/TrackView (Sprint 4) — có current_roi_id.
        person_count: Số người trong frame.
        nearest_distance: Khoảng cách tới người gần nhất (px) hoặc None.
        low_motion_speed: Ngưỡng ít chuyển động.
        nearby_distance: Ngưỡng "ở gần" người khác.
        desk_roi_configured: True nếu camera có polygon bàn làm việc.

    Returns:
        dict facts.
    """
    head = getattr(dto, "head", None)
    hand = getattr(dto, "hand", None)
    motion = getattr(dto, "motion", None)
    chair = getattr(dto, "chair_feature", None)
    phone = getattr(dto, "phone_feature", None)
    food = getattr(dto, "food_feature", None)

    looking = _looking(dto)
    movement_speed = float(getattr(motion, "movement_speed", 0.0) or 0.0)
    hand_on_desk = bool(getattr(chair, "hand_on_desk", False))
    looking_monitor = looking == "MONITOR"
    working = hand_on_desk or looking_monitor

    roi_id = getattr(track, "current_roi_id", None)
    body_in_roi = bool(getattr(chair, "body_in_roi", False)) or roi_id is not None

    # Có ROI bàn: rời chỗ = ngoài ROI.
    # Không ROI (1 camera ≈ 1 bàn): người còn trong khung = đang ở bàn;
    # vắng mặt xử lý bằng desk-absence ở RuleEngine.
    if desk_roi_configured:
        away_from_desk = not body_in_roi
    else:
        away_from_desk = False

    food_visible = bool(
        getattr(food, "food_mouth", None) is not None
        or getattr(food, "cup_mouth", None) is not None
        or getattr(food, "bottle_mouth", None) is not None
    )

    phone_visible = bool(getattr(phone, "visible", False))
    hand_near = bool(getattr(hand, "near_phone", False))
    person_bbox = getattr(track, "bbox", None)
    phone_bbox = getattr(phone, "bbox", None) if phone is not None else None

    return {
        "phone_detected": phone_visible,
        "hand_near_phone": hand_near,
        "phone_person_near": phone_visible and hand_near,
        "looking_phone": looking == "PHONE",
        "looking_monitor": looking_monitor,
        "head_down": getattr(head, "direction", "") == "DOWN",
        "head_direction": getattr(head, "direction", "UNKNOWN"),
        "head_angle": float(getattr(head, "angle", 0.0) or 0.0),
        "movement_speed": movement_speed,
        "stationary": getattr(motion, "direction", "") == "STATIONARY",
        "stationary_time": float(getattr(motion, "stationary_time", 0.0) or 0.0),
        "low_motion": movement_speed < low_motion_speed,
        "sitting": bool(getattr(chair, "sitting", False)),
        "hand_on_desk": hand_on_desk,
        "hand_near_face": bool(getattr(hand, "near_face", False)),
        "working": working,
        "in_roi": body_in_roi,
        "roi": roi_id,
        "away_from_desk": away_from_desk,
        "food_visible": food_visible,
        "food_near_mouth": bool(getattr(food, "near_mouth", False)),
        "person_count": int(person_count),
        "nearest_person_distance": nearest_distance,
        "has_nearby_person": (
            nearest_distance is not None and nearest_distance < nearby_distance
        ),
        # Evidence snapshot (không dùng trong rule condition)
        "person_bbox": list(person_bbox) if person_bbox is not None else None,
        "phone_bbox": list(phone_bbox) if phone_bbox is not None else None,
    }


def estimate_confidence(dto: Any, track: Any) -> float:
    """
    Ước lượng confidence cho event từ chất lượng feature.

    Kết hợp score track + độ ổn định đầu + tính khả dụng của pose.
    """
    base = 0.8
    head = getattr(dto, "head", None)
    if head is not None and getattr(head, "available", False):
        base += 0.1 * float(getattr(head, "stability", 0.0) or 0.0)
    score = getattr(track, "score", None)
    if score is not None:
        base = (base + float(score)) / 2.0
    return round(min(1.0, max(0.0, base)), 4)
