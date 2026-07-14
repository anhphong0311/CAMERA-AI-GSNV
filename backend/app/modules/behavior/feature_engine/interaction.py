"""
InteractionExtractor — đặc trưng tương tác: điện thoại, đồ ăn, ghế/bàn.

Chỉ tính khoảng cách/visibility/hướng. KHÔNG tạo alert, KHÔNG rule.
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.modules.behavior.config import ThresholdConfig
from app.modules.behavior.feature_engine.context import ObjectContext
from app.modules.behavior.models import (
    ChairFeature,
    FoodFeature,
    Keypoints,
    PhoneFeature,
)
from app.modules.behavior.models.keypoints import (
    LEFT_SHOULDER,
    LEFT_WRIST,
    NOSE,
    RIGHT_SHOULDER,
    RIGHT_WRIST,
)
from app.modules.behavior.utils.geometry import (
    bbox_center,
    bbox_iou,
    distance,
    midpoint,
    scale_from,
)

BBox = Tuple[float, float, float, float]
Point = Tuple[float, float]


class InteractionExtractor:
    """Trích đặc trưng tương tác điện thoại / đồ ăn / ghế-bàn."""

    def __init__(self, thresholds: ThresholdConfig) -> None:
        self._t = thresholds

    def _hands(self, kpts: Keypoints) -> list[Point]:
        return [p for p in (kpts.get(LEFT_WRIST), kpts.get(RIGHT_WRIST)) if p]

    def _phone_near_person(
        self, phone_box: BBox, person_bbox: BBox, kpts: Keypoints
    ) -> bool:
        """Phone thuộc người này — gần tay/khung người; nới cho góc desk/cận cảnh."""
        px1, py1, px2, py2 = person_bbox
        pw, ph = max(px2 - px1, 1.0), max(py2 - py1, 1.0)
        cx, cy = bbox_center(phone_box)
        hands = self._hands(kpts)
        near_px = max(self._t.hand_near_phone_px, 120.0)

        for hand in hands:
            d = distance(hand, (cx, cy))
            if d is not None and d < near_px * 1.5:
                return True

        # Phone chồng lên bbox người (cầm trong tay / che thân)
        if bbox_iou(phone_box, person_bbox) > 0.01:
            return True

        # Vùng quanh người (kể cả dưới eo — cầm phone ngồi bàn)
        margin_x = pw * 0.35
        margin_y = ph * 0.25
        if (px1 - margin_x) <= cx <= (px2 + margin_x) and (
            py1 - margin_y
        ) <= cy <= (py2 + margin_y):
            return True
        return False

    def phone(
        self,
        kpts: Keypoints,
        ctx: ObjectContext,
        person_bbox: Optional[BBox] = None,
    ) -> Tuple[PhoneFeature, bool]:
        """
        Đặc trưng điện thoại (chỉ xét phone gần người — không lấy đồ trên bàn).

        Returns:
            (PhoneFeature, near) — near dùng cho gaze/hand.
        """
        phones = ctx.boxes("phone")
        if person_bbox is not None:
            phones = [
                p for p in phones if self._phone_near_person(p, person_bbox, kpts)
            ]
        visible = len(phones) > 0
        feature = PhoneFeature(visible=visible)
        if not visible:
            return feature, False

        # Giữ bbox phone gần tay/người nhất để snapshot evidence
        hands = self._hands(kpts)
        near_px = max(self._t.hand_near_phone_px, 120.0)
        best_box: Optional[BBox] = phones[0]
        best_score: Optional[float] = None
        for pbox in phones:
            score: Optional[float] = None
            if hands:
                dists = []
                for hand in hands:
                    d = distance(hand, bbox_center(pbox))
                    if d is not None:
                        dists.append(d)
                if dists:
                    score = min(dists)
            if score is None and person_bbox is not None:
                score = distance(bbox_center(person_bbox), bbox_center(pbox))
            if score is not None and (best_score is None or score < best_score):
                best_score = score
                best_box = pbox
        feature.bbox = best_box

        # Không có cổ tay (pose yếu / cận cảnh) nhưng phone đã gắn người → coi như đang dùng
        if not hands:
            feature.near = True
            feature.distance_hand = best_score
            return feature, True

        feature.distance_hand = best_score
        feature.near = best_score is not None and best_score < near_px * 1.5
        # Phone chồng bbox người → vẫn near dù khoảng cách wrist hơi xa
        if not feature.near and person_bbox is not None:
            for pbox in phones:
                if bbox_iou(pbox, person_bbox) > 0.01:
                    feature.near = True
                    feature.bbox = pbox
                    break
        return feature, feature.near

    def food(
        self, kpts: Keypoints, bbox: BBox, ctx: ObjectContext
    ) -> FoodFeature:
        """Đặc trưng đồ ăn/uống — khoảng cách tới miệng (proxy = mũi)."""
        mouth = kpts.get(NOSE)
        feature = FoodFeature()
        if mouth is None:
            return feature

        scale = scale_from(kpts.get(LEFT_SHOULDER), kpts.get(RIGHT_SHOULDER), bbox)
        near_thresh = self._t.food_near_mouth_ratio * scale

        hands = self._hands(kpts)
        hand_mouth = None
        for hand in hands:
            d = distance(hand, mouth)
            if d is not None and (hand_mouth is None or d < hand_mouth):
                hand_mouth = d
        feature.hand_mouth = hand_mouth
        feature.food_mouth = ctx.nearest_distance("food", mouth)
        feature.cup_mouth = ctx.nearest_distance("cup", mouth)
        feature.bottle_mouth = ctx.nearest_distance("bottle", mouth)

        candidates = [
            v
            for v in (
                feature.food_mouth,
                feature.cup_mouth,
                feature.bottle_mouth,
            )
            if v is not None
        ]
        feature.near_mouth = any(v < near_thresh for v in candidates)
        return feature

    def desk(
        self,
        kpts: Keypoints,
        bbox: BBox,
        ctx: ObjectContext,
        posture: str,
        sitting: bool,
        body_in_roi: bool,
    ) -> ChairFeature:
        """Đặc trưng ghế/bàn (desk interaction)."""
        feature = ChairFeature(
            sitting=sitting,
            posture=posture,
            body_in_roi=body_in_roi,
        )

        # Chair detection: ghế chồng lấn khung người
        for chair in ctx.boxes("chair"):
            if bbox_iou(bbox, chair) > 0.05:
                feature.chair_detected = True
                break

        # Hand on desk: cổ tay nằm ở nửa dưới khung người (ước lượng mặt bàn)
        y_top, y_bottom = bbox[1], bbox[3]
        desk_line = y_top + (y_bottom - y_top) * 0.6
        for w in self._hands(kpts):
            if w[1] >= desk_line:
                feature.hand_on_desk = True
                break

        # Monitor direction: monitor ở trái/phải/giữa so với người
        monitor = ctx.nearest_box("monitor", bbox_center(bbox))
        if monitor is not None:
            mx = bbox_center(monitor)[0]
            px = bbox_center(bbox)[0]
            scale = scale_from(
                kpts.get(LEFT_SHOULDER), kpts.get(RIGHT_SHOULDER), bbox
            )
            if mx < px - scale * 0.5:
                feature.monitor_direction = "LEFT"
            elif mx > px + scale * 0.5:
                feature.monitor_direction = "RIGHT"
            else:
                feature.monitor_direction = "CENTER"

        return feature
