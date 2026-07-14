"""
RuleEngine — orchestrator suy luận hành vi cho MỘT camera.

Pipeline: BehaviorFeatureDTO → Facts → Condition → Evaluation → Event → Action.
Quản lý state machine, cooldown, duplicate filter, temporal analysis, performance.
KHÔNG Telegram/DB/Dashboard. Track ID độc lập theo camera.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.modules.rule_engine.action import ActionExecutor, AlertQueue
from app.modules.rule_engine.cache import CooldownCache, DuplicateFilter
from app.modules.rule_engine.config import (
    CooldownConfig,
    RuleEngineConfig,
)
from app.modules.rule_engine.event.event import BehaviorEventDTO
from app.modules.rule_engine.event.severity import Severity
from app.modules.rule_engine.repositories import EventRepository, RuleRepository
from app.modules.rule_engine.rule_engine.facts import build_facts, estimate_confidence
from app.modules.rule_engine.rule_engine.performance import PerformanceScoreCalculator
from app.modules.rule_engine.rule_executor import RuleExecutor
from app.modules.rule_engine.rule_history import RuleHistory
from app.modules.rule_engine.rule_parser.rule import Rule
from app.modules.rule_engine.rule_scheduler import RuleScheduler
from app.modules.rule_engine.state import EventState, StateStore
from app.modules.rule_engine.timeline import TemporalTracker

try:
    from app.modules.event.evidence.config import load_evidence_config
except ImportError:  # pragma: no cover
    load_evidence_config = None  # type: ignore

# Track ảo: 1 camera ≈ 1 bàn khi chưa cấu hình ROI polygon
DESK_ABSENCE_TRACK_ID = 0


class RuleEngine:
    """Suy luận hành vi cho một camera."""

    def __init__(
        self,
        camera_id: int,
        rule_repo: RuleRepository,
        event_repo: EventRepository,
        alert_queue: AlertQueue,
        config: RuleEngineConfig,
        cooldown_config: CooldownConfig,
    ) -> None:
        self.camera_id = camera_id
        self._rules = rule_repo
        self._events = event_repo
        self._config = config
        self._cooldown_config = cooldown_config
        self._executor = RuleExecutor()
        self._states = StateStore(config.max_states)
        self._cooldown = CooldownCache()
        self._duplicate = DuplicateFilter(config.duplicate_window)
        self._temporal = TemporalTracker(config.temporal_windows)
        self._history = RuleHistory()
        self._actions = ActionExecutor(alert_queue)
        self._perf = PerformanceScoreCalculator(config.performance.weights)
        self._track_clock: Dict[int, datetime] = {}
        self._desk_roi_cached: Optional[bool] = None

        self._scheduler = RuleScheduler(interval_seconds=30.0)
        self._scheduler.add_task(self._cooldown.cleanup)
        self._scheduler.add_task(self._duplicate.cleanup)
        self._scheduler.add_task(self._temporal.prune)
        max_idle = (config.temporal_windows[-1] if config.temporal_windows else 300) * 2
        self._scheduler.add_task(
            lambda now: self._states.prune_stale(now, max_idle)
        )
        self._evidence_cfg = (
            load_evidence_config() if load_evidence_config else None
        )

    @property
    def performance(self) -> PerformanceScoreCalculator:
        """Bộ tính điểm hiệu suất của camera."""
        return self._perf

    @property
    def history(self) -> RuleHistory:
        """Lịch sử thực thi rule."""
        return self._history

    def _cooldown_seconds(self, rule: Rule) -> float:
        """Cooldown áp dụng cho rule (ưu tiên field rule → cooldown.yaml)."""
        if rule.cooldown is not None:
            return rule.cooldown
        return self._cooldown_config.for_rule(rule.id)

    def _desk_roi_configured(self) -> bool:
        """Camera có polygon bàn làm việc trong tracking.yaml hay không."""
        if self._desk_roi_cached is not None:
            return self._desk_roi_cached
        try:
            from app.modules.tracking.config.loader import load_tracking_config

            cfg = load_tracking_config()
            regions = list(getattr(cfg.roi, "regions", None) or [])
            cameras = dict(getattr(cfg.roi, "cameras", None) or {})
            cam_key = str(self.camera_id)
            cam_regions = cameras.get(cam_key) or cameras.get(self.camera_id) or []
            self._desk_roi_cached = bool(regions) or bool(cam_regions)
        except Exception:
            self._desk_roi_cached = False
        return self._desk_roi_cached

    def process(
        self, detection_result: Any, tracking_result: Any, behavior_result: Any
    ) -> List[BehaviorEventDTO]:
        """
        Chạy rule cho một frame.

        Args:
            detection_result: DetectionResult (ngữ cảnh; có thể None).
            tracking_result: TrackingResult (tracks).
            behavior_result: BehaviorResult (features per track).

        Returns:
            Danh sách event mới được xác nhận trong frame này.
        """
        now: datetime = behavior_result.timestamp
        self._scheduler.tick(now)

        tracks = list(getattr(tracking_result, "tracks", []))
        track_map = {t.track_id: t for t in tracks}
        centers = {t.track_id: t.center for t in tracks}
        person_count = max(
            getattr(behavior_result, "count", 0), len(tracks)
        )
        desk_roi = self._desk_roi_configured()

        rules = self._rules.enabled_rules()
        created: List[BehaviorEventDTO] = []
        frame_index = getattr(detection_result, "frame_id", None)
        seen_track_ids = {dto.track_id for dto in behavior_result.features}

        for dto in behavior_result.features:
            track_id = dto.track_id
            track = track_map.get(track_id, dto)
            nearest = self._nearest_distance(track_id, centers)
            facts = build_facts(
                dto,
                track,
                person_count,
                nearest,
                self._config.low_motion_speed,
                self._config.nearby_person_distance,
                desk_roi_configured=desk_roi,
            )
            confidence = estimate_confidence(dto, track)

            # track clock (dt dùng cho performance)
            last_seen = self._track_clock.get(track_id)
            track_dt = (now - last_seen).total_seconds() if last_seen else 0.0
            self._track_clock[track_id] = now

            active_categories: Dict[str, bool] = {}
            for rule in rules:
                state = self._states.get_or_create(rule.id, track_id, self.camera_id)
                dt = (
                    (now - state.last_ts).total_seconds()
                    if state.last_ts is not None
                    else 0.0
                )
                result = self._executor.execute(
                    rule,
                    facts,
                    state,
                    now,
                    dt,
                    gap_reset_seconds=self._gap_reset(rule),
                    frame_index=frame_index,
                )
                self._temporal.record(rule.id, track_id, now, result.base_active)
                self._history.record(
                    now,
                    rule.id,
                    track_id,
                    self.camera_id,
                    result.base_active,
                    result.fired,
                )
                if rule.category:
                    active_categories[rule.category] = result.base_active
                self._handle_event(
                    rule, state, result, now, track_id, confidence, facts, created
                )

            self._perf.update(
                track_id,
                self.camera_id,
                track_dt,
                active_categories,
                bool(facts.get("working")),
            )

        # Track biến mất khỏi frame → kết thúc event đang mở
        # (giữ track vắng bàn ảo — xử lý riêng bên dưới)
        self._finalize_missing_tracks(
            rules,
            seen_track_ids | {DESK_ABSENCE_TRACK_ID},
            now,
            created,
        )

        # Không ROI: 1 camera ≈ 1 bàn → phát hiện bàn trống theo person_count
        if not desk_roi:
            if person_count <= 0:
                self._process_desk_absence(rules, now, created, frame_index)
            else:
                self._clear_desk_absence(rules, now, created)

        return created

    def _gap_reset(self, rule: Rule) -> Optional[float]:
        """Gap reset cho phone timer (giây)."""
        if self._evidence_cfg is None:
            return None
        return self._evidence_cfg.gap_reset_for_rule(rule.id)

    # Không trì hoãn alert AWAY — gửi ngay khi đủ thời gian (ảnh bàn trống).
    _NOTIFY_ON_FINISH: frozenset[str] = frozenset()

    def _absence_facts(self) -> Dict[str, Any]:
        return {
            "away_from_desk": True,
            "in_roi": False,
            "person_count": 0,
            "phone_detected": False,
            "hand_near_phone": False,
            "phone_person_near": False,
            "looking_phone": False,
            "working": False,
            "sitting": False,
            "stationary": True,
            "low_motion": True,
            "food_visible": False,
            "food_near_mouth": False,
            "has_nearby_person": False,
            "nearest_person_distance": None,
        }

    def _process_desk_absence(
        self,
        rules: List[Rule],
        now: datetime,
        created: List[BehaviorEventDTO],
        frame_index: Optional[int],
    ) -> None:
        """Bàn trống (không còn người trong khung) — chạy AWAY_FROM_DESK."""
        rule = next((r for r in rules if r.id == "AWAY_FROM_DESK"), None)
        if rule is None:
            return
        track_id = DESK_ABSENCE_TRACK_ID
        facts = self._absence_facts()
        state = self._states.get_or_create(rule.id, track_id, self.camera_id)
        dt = (
            (now - state.last_ts).total_seconds() if state.last_ts is not None else 0.0
        )
        result = self._executor.execute(
            rule,
            facts,
            state,
            now,
            dt,
            gap_reset_seconds=self._gap_reset(rule),
            frame_index=frame_index,
        )
        self._temporal.record(rule.id, track_id, now, result.base_active)
        self._history.record(
            now, rule.id, track_id, self.camera_id, result.base_active, result.fired
        )
        self._handle_event(
            rule, state, result, now, track_id, 0.9, facts, created
        )

    def _clear_desk_absence(
        self,
        rules: List[Rule],
        now: datetime,
        created: List[BehaviorEventDTO],
    ) -> None:
        """Người đã quay lại khung hình — đóng event vắng bàn (không gửi lại)."""
        rule = next((r for r in rules if r.id == "AWAY_FROM_DESK"), None)
        if rule is None:
            return
        state = self._states.get_or_create(
            rule.id, DESK_ABSENCE_TRACK_ID, self.camera_id
        )
        if state.current_event is not None:
            self._finish_event(rule, state, now, created, notify=False)
        state.reset_activity()
        state.last_ts = now
        state.lifecycle = "WAITING"

    def _handle_event(
        self,
        rule: Rule,
        state,
        result,
        now: datetime,
        track_id: int,
        confidence: float,
        facts: Dict[str, Any],
        created: List[BehaviorEventDTO],
    ) -> None:
        """Quản lý vòng đời event theo kết quả rule."""
        if result.fired:
            if state.current_event is None:
                if self._cooldown.active(
                    rule.id, track_id, now
                ) or self._duplicate.is_duplicate(rule.id, track_id, now):
                    logger.debug(
                        "Event IGNORED (cooldown/duplicate) rule={} track={}",
                        rule.id,
                        track_id,
                    )
                    return
                meta = self._metadata(rule, facts, now, track_id, state)
                if rule.id == "AWAY_FROM_DESK":
                    meta["empty_desk"] = True
                    meta["snapshot_hint"] = "empty_workstation"
                if rule.id == "PHONE_USAGE":
                    meta["snapshot_hint"] = "phone_usage"
                    if facts.get("person_bbox"):
                        meta["person_bbox"] = facts["person_bbox"]
                    if facts.get("phone_bbox"):
                        meta["phone_bbox"] = facts["phone_bbox"]
                event = BehaviorEventDTO(
                    camera_id=self.camera_id,
                    track_id=track_id,
                    rule_id=rule.id,
                    event_type=rule.id,
                    severity=rule.severity,
                    start_time=state.active_since or now,
                    confidence=confidence,
                    state=EventState.CONFIRMED,
                    end_time=now,
                    duration=state.active_seconds,
                    metadata=meta,
                )
                self._events.add(event)
                self._duplicate.record(rule.id, track_id, now)
                # Gửi alert ngay khi đủ ngưỡng (AWAY = ảnh bàn trống lúc này)
                if rule.id not in self._NOTIFY_ON_FINISH:
                    self._actions.execute(rule.actions, event)
                state.current_event = event
                state.lifecycle = "CONFIRMED"
                created.append(event)
                logger.info(
                    "Event created rule={} track={} severity={} conf={:.2f}",
                    rule.id,
                    track_id,
                    rule.severity.value,
                    confidence,
                )
            else:
                ev = state.current_event
                ev.end_time = now
                ev.duration = state.active_seconds
                ev.state = EventState.CONFIRMED
        else:
            if state.current_event is not None and not result.base_active:
                self._finish_event(rule, state, now, created)

    def _finish_event(
        self,
        rule: Rule,
        state,
        now: datetime,
        created: List[BehaviorEventDTO],
        *,
        notify: bool = True,
    ) -> None:
        """Kết thúc event đang mở; với PHONE/AWAY đẩy alert kèm end_time."""
        ev = state.current_event
        if ev is None:
            return
        track_id = ev.track_id
        ev.state = EventState.FINISHED
        ev.end_time = now
        if ev.start_time is not None:
            ev.duration = max(0.0, (now - ev.start_time).total_seconds())
        else:
            ev.duration = state.active_seconds
        meta = dict(ev.metadata or {})
        meta["lifecycle"] = "FINISHED"
        meta["ended_at"] = now.isoformat()
        ev.metadata = meta
        self._events.end(ev)
        state.lifecycle = "FINISHED"
        self._cooldown.start(rule.id, track_id, now, self._cooldown_seconds(rule))
        state.current_event = None
        if notify and rule.id in self._NOTIFY_ON_FINISH and "alert" in (
            a.lower() for a in rule.actions
        ):
            self._actions.execute(rule.actions, ev)
            created.append(ev)
        logger.info(
            "Event ended rule={} track={} duration={:.1f}s start={} end={}",
            rule.id,
            track_id,
            ev.duration,
            ev.start_time.isoformat() if ev.start_time else None,
            now.isoformat(),
        )

    def _finalize_missing_tracks(
        self,
        rules: List[Rule],
        seen_track_ids: set[int],
        now: datetime,
        created: List[BehaviorEventDTO],
    ) -> None:
        """Track không còn trong frame → kết thúc event mở (coi như quay lại / dừng hành vi)."""
        rule_by_id = {r.id: r for r in rules}
        for state in self._states.all_states():
            if state.current_event is None:
                continue
            if state.track_id in seen_track_ids:
                continue
            rule = rule_by_id.get(state.rule_id)
            if rule is None:
                continue
            self._finish_event(rule, state, now, created)

    def _metadata(
        self, rule: Rule, facts: Dict[str, Any], now: datetime, track_id: int, state
    ) -> Dict[str, Any]:
        """Metadata kèm event (facts + temporal + evidence)."""
        keys = rule.condition.required_facts()
        snapshot = {k: facts.get(k) for k in keys}
        meta: Dict[str, Any] = {
            "facts": snapshot,
            "temporal": self._temporal.summary(rule.id, track_id, now),
            "severity_rank": rule.severity.rank,
            "lifecycle": state.lifecycle,
        }
        if state.evidence_time is not None:
            meta["evidence_time"] = state.evidence_time.isoformat()
        if state.start_frame_index is not None:
            meta["start_frame_index"] = state.start_frame_index
        return meta

    def _nearest_distance(
        self, track_id: int, centers: Dict[int, tuple]
    ) -> Optional[float]:
        """Khoảng cách tới người gần nhất (px)."""
        me = centers.get(track_id)
        if me is None:
            return None
        best: Optional[float] = None
        for tid, c in centers.items():
            if tid == track_id:
                continue
            d = math.hypot(me[0] - c[0], me[1] - c[1])
            if best is None or d < best:
                best = d
        return best

    def statistics(self) -> Dict[str, Any]:
        """Thống kê engine của camera."""
        return {
            "camera_id": self.camera_id,
            "states": self._states.count,
            "rule_history": self._history.stats(),
            "performance_tracks": len(self._perf.all_reports()),
        }

    def clear(self) -> None:
        """Xóa toàn bộ state (giữ rules)."""
        self._states.clear()
        self._cooldown.clear()
        self._duplicate.clear()
        self._temporal.clear()
        self._history.clear()
        self._perf.clear()
        self._track_clock.clear()
