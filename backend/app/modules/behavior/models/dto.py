"""
DTO — BehaviorFeatureDTO (một track) và BehaviorResult (một frame).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List

from app.modules.behavior.models.features import (
    BodyFeature,
    ChairFeature,
    FoodFeature,
    GazeFeature,
    HandFeature,
    HeadFeature,
    MotionFeature,
    PhoneFeature,
    TemporalFeature,
)


@dataclass
class BehaviorFeatureDTO:
    """
    Đặc trưng hành vi cho MỘT track — DTO chuẩn để Rule Engine (Sprint 6) dùng.
    """

    track_id: int
    timestamp: datetime
    head: HeadFeature = field(default_factory=HeadFeature)
    body: BodyFeature = field(default_factory=BodyFeature)
    hand: HandFeature = field(default_factory=HandFeature)
    gaze: GazeFeature = field(default_factory=GazeFeature)
    motion: MotionFeature = field(default_factory=MotionFeature)
    phone_feature: PhoneFeature = field(default_factory=PhoneFeature)
    food_feature: FoodFeature = field(default_factory=FoodFeature)
    chair_feature: ChairFeature = field(default_factory=ChairFeature)
    temporal_feature: TemporalFeature = field(default_factory=TemporalFeature)

    def to_dict(self) -> dict[str, Any]:
        """Serialize BehaviorFeatureDTO."""
        return {
            "track_id": self.track_id,
            "timestamp": self.timestamp.isoformat(),
            "head": self.head.to_dict(),
            "body": self.body.to_dict(),
            "hand": self.hand.to_dict(),
            "gaze": self.gaze.to_dict(),
            "motion": self.motion.to_dict(),
            "phone_feature": self.phone_feature.to_dict(),
            "food_feature": self.food_feature.to_dict(),
            "chair_feature": self.chair_feature.to_dict(),
            "temporal_feature": self.temporal_feature.to_dict(),
        }


@dataclass
class BehaviorResult:
    """Đặc trưng hành vi cho một frame (nhiều track)."""

    camera_id: int
    frame_id: int
    timestamp: datetime
    features: List[BehaviorFeatureDTO] = field(default_factory=list)
    processing_time_ms: float = 0.0

    @property
    def count(self) -> int:
        """Số người có feature."""
        return len(self.features)

    def to_dict(self) -> dict[str, Any]:
        """Serialize BehaviorResult."""
        return {
            "camera_id": self.camera_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "features": [f.to_dict() for f in self.features],
            "count": self.count,
            "processing_time_ms": round(self.processing_time_ms, 2),
        }
