"""
DTO — các đặc trưng hành vi (feature). Tất cả là ƯỚC LƯỢNG, không khẳng định.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class HeadFeature:
    """Đặc trưng đầu."""

    position: Optional[Tuple[float, float]] = None
    angle: float = 0.0
    direction: str = "UNKNOWN"  # FORWARD/DOWN/UP/LEFT/RIGHT/UNKNOWN
    stability: float = 1.0  # 0..1 (cao = ổn định)
    available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": [round(self.position[0], 1), round(self.position[1], 1)]
            if self.position
            else None,
            "angle": round(self.angle, 1),
            "direction": self.direction,
            "stability": round(self.stability, 3),
            "available": self.available,
        }


@dataclass
class BodyFeature:
    """Đặc trưng thân."""

    angle: float = 0.0
    lean: str = "UNKNOWN"  # FORWARD/BACK/NEUTRAL/UNKNOWN
    rotation: float = 0.0
    available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "angle": round(self.angle, 1),
            "lean": self.lean,
            "rotation": round(self.rotation, 1),
            "available": self.available,
        }


@dataclass
class HandFeature:
    """Đặc trưng tay."""

    left_position: Optional[Tuple[float, float]] = None
    right_position: Optional[Tuple[float, float]] = None
    movement: float = 0.0  # px kể từ frame trước (max 2 tay)
    speed: float = 0.0  # px/frame
    near_face: bool = False
    near_phone: bool = False
    distance_phone: Optional[float] = None
    available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_position": list(self.left_position) if self.left_position else None,
            "right_position": list(self.right_position)
            if self.right_position
            else None,
            "movement": round(self.movement, 2),
            "speed": round(self.speed, 2),
            "near_face": self.near_face,
            "near_phone": self.near_phone,
            "distance_phone": round(self.distance_phone, 1)
            if self.distance_phone is not None
            else None,
            "available": self.available,
        }


@dataclass
class GazeFeature:
    """Đặc trưng hướng nhìn (ước lượng)."""

    looking: str = "UNKNOWN"  # MONITOR/PHONE/LEFT/RIGHT/DOWN/FORWARD/UNKNOWN
    confidence: float = 0.0  # mức độ tin cậy ước lượng 0..1

    def to_dict(self) -> dict[str, Any]:
        return {"looking": self.looking, "confidence": round(self.confidence, 3)}


@dataclass
class MotionFeature:
    """Đặc trưng chuyển động."""

    stationary_time: float = 0.0  # giây đứng yên liên tục
    movement_distance: float = 0.0  # px tổng quãng gần đây
    movement_speed: float = 0.0  # px/frame
    direction: str = "STATIONARY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "stationary_time": round(self.stationary_time, 2),
            "movement_distance": round(self.movement_distance, 1),
            "movement_speed": round(self.movement_speed, 2),
            "direction": self.direction,
        }


@dataclass
class PhoneFeature:
    """Đặc trưng tương tác điện thoại (KHÔNG alert)."""

    visible: bool = False
    distance_hand: Optional[float] = None
    near: bool = False
    duration: float = 0.0  # giây tay gần điện thoại liên tục
    bbox: Optional[Tuple[float, float, float, float]] = None  # xyxy phone gần người

    def to_dict(self) -> dict[str, Any]:
        return {
            "visible": self.visible,
            "distance_hand": round(self.distance_hand, 1)
            if self.distance_hand is not None
            else None,
            "near": self.near,
            "duration": round(self.duration, 2),
            "bbox": [round(v, 1) for v in self.bbox] if self.bbox else None,
        }


@dataclass
class FoodFeature:
    """Đặc trưng ăn uống (khoảng cách tới miệng, ước lượng)."""

    hand_mouth: Optional[float] = None
    food_mouth: Optional[float] = None
    cup_mouth: Optional[float] = None
    bottle_mouth: Optional[float] = None
    near_mouth: bool = False

    def to_dict(self) -> dict[str, Any]:
        def r(v):
            return round(v, 1) if v is not None else None

        return {
            "hand_mouth": r(self.hand_mouth),
            "food_mouth": r(self.food_mouth),
            "cup_mouth": r(self.cup_mouth),
            "bottle_mouth": r(self.bottle_mouth),
            "near_mouth": self.near_mouth,
        }


@dataclass
class ChairFeature:
    """Đặc trưng ghế/bàn (desk interaction)."""

    sitting: bool = False
    posture: str = "UNKNOWN"  # SITTING/STANDING/UNKNOWN
    chair_detected: bool = False
    leaving_chair: bool = False
    returning_chair: bool = False
    hand_on_desk: bool = False
    body_in_roi: bool = False
    monitor_direction: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sitting": self.sitting,
            "posture": self.posture,
            "chair_detected": self.chair_detected,
            "leaving_chair": self.leaving_chair,
            "returning_chair": self.returning_chair,
            "hand_on_desk": self.hand_on_desk,
            "body_in_roi": self.body_in_roi,
            "monitor_direction": self.monitor_direction,
        }


@dataclass
class TemporalFeature:
    """Đặc trưng thời gian (kích thước history buffer)."""

    buffer_size: int = 0
    pose_history: int = 0
    motion_history: int = 0
    head_history: int = 0
    hand_history: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "buffer_size": self.buffer_size,
            "pose_history": self.pose_history,
            "motion_history": self.motion_history,
            "head_history": self.head_history,
            "hand_history": self.hand_history,
        }
