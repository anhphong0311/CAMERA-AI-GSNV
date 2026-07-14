"""
RuleService — facade đa camera cho Rule Engine.

Quản lý Rule (CRUD, enable/disable, reload), điều phối RuleEngine mỗi camera,
truy vấn Event + Performance Score. KHÔNG Telegram/DB/Dashboard.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.modules.rule_engine.action import AlertQueue
from app.modules.rule_engine.config import (
    CooldownConfig,
    RuleEngineConfig,
    load_cooldown_config,
    load_rule_engine_config,
    rules_config_path,
)
from app.modules.rule_engine.event.event import BehaviorEventDTO
from app.modules.rule_engine.repositories import EventRepository, RuleRepository
from app.modules.rule_engine.rule_engine.engine import RuleEngine
from app.modules.rule_engine.rule_parser import (
    Rule,
    load_rules_from_file,
    parse_rule,
)
from app.modules.rule_engine.rule_validator import validate_rule


class RuleService:
    """Facade Rule Engine cho nhiều camera."""

    def __init__(
        self,
        config: Optional[RuleEngineConfig] = None,
        cooldown_config: Optional[CooldownConfig] = None,
    ) -> None:
        self._config = config or load_rule_engine_config()
        self._cooldown_config = cooldown_config or load_cooldown_config()
        self._rules = RuleRepository()
        self._events = EventRepository()
        self._alert_queue = AlertQueue()
        self._engines: Dict[int, RuleEngine] = {}
        self._lock = threading.RLock()

    # ----- lifecycle / seed -----
    def load_rules_file(self, path: Optional[str | Path] = None) -> int:
        """Nạp rule từ rules.yaml (seed ban đầu). Trả số rule nạp được."""
        p = Path(path) if path else rules_config_path()
        try:
            rules = load_rules_from_file(p)
        except Exception as exc:  # pragma: no cover
            logger.warning("Không nạp được rules từ {}: {}", p, exc)
            return 0
        count = 0
        for rule in rules:
            try:
                validate_rule(rule)
                self._rules.upsert(rule)
                count += 1
                logger.info("Rule loaded: {} ({})", rule.id, rule.severity.value)
            except Exception as exc:
                logger.warning("Bỏ qua rule không hợp lệ {}: {}", rule.id, exc)
        return count

    def _engine(self, camera_id: int) -> RuleEngine:
        """Lấy/tạo engine cho camera."""
        eng = self._engines.get(camera_id)
        if eng is None:
            eng = RuleEngine(
                camera_id=camera_id,
                rule_repo=self._rules,
                event_repo=self._events,
                alert_queue=self._alert_queue,
                config=self._config,
                cooldown_config=self._cooldown_config,
            )
            self._engines[camera_id] = eng
        return eng

    # ----- processing -----
    def process(
        self, detection_result: Any, tracking_result: Any, behavior_result: Any
    ) -> List[BehaviorEventDTO]:
        """Chạy rule cho một frame (route theo camera_id)."""
        camera_id = behavior_result.camera_id
        with self._lock:
            engine = self._engine(camera_id)
        return engine.process(detection_result, tracking_result, behavior_result)

    # ----- rule CRUD -----
    def list_rules(self) -> List[Rule]:
        """Danh sách rule."""
        return self._rules.list()

    def get_rule(self, rule_id: str) -> Rule:
        """Lấy rule."""
        return self._rules.require(rule_id)

    def add_rule(self, raw: Dict[str, Any]) -> Rule:
        """Thêm rule mới từ dict (JSON/YAML đã parse)."""
        rule = parse_rule(raw)
        validate_rule(rule)
        return self._rules.add(rule)

    def update_rule(self, rule_id: str, raw: Dict[str, Any]) -> Rule:
        """Cập nhật rule."""
        self._rules.require(rule_id)
        raw = {**raw, "id": rule_id}
        rule = parse_rule(raw)
        validate_rule(rule)
        return self._rules.update(rule)

    def delete_rule(self, rule_id: str) -> None:
        """Xóa rule."""
        self._rules.delete(rule_id)

    def set_enabled(self, rule_id: str, enabled: bool) -> Rule:
        """Bật/tắt rule."""
        rule = self._rules.set_enabled(rule_id, enabled)
        logger.info("Rule {} {}", rule_id, "enabled" if enabled else "disabled")
        return rule

    # ----- events -----
    def live_events(self) -> List[BehaviorEventDTO]:
        """Event đang hoạt động."""
        return self._events.live()

    def event_history(
        self,
        camera_id: Optional[int] = None,
        track_id: Optional[int] = None,
        rule_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[BehaviorEventDTO]:
        """Lịch sử event."""
        return self._events.history(camera_id, track_id, rule_id, limit)

    def alert_queue(self) -> AlertQueue:
        """Truy cập AlertQueue (Sprint 7)."""
        return self._alert_queue

    # ----- performance -----
    def performance_reports(self) -> List[Dict[str, Any]]:
        """Báo cáo điểm hiệu suất tất cả camera/track."""
        reports: List[Dict[str, Any]] = []
        for engine in self._engines.values():
            reports.extend(engine.performance.all_reports())
        return reports

    def performance_for_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        """Báo cáo điểm cho một track (tìm khắp camera)."""
        for engine in self._engines.values():
            reports = engine.performance.all_reports()
            for r in reports:
                if r["track_id"] == track_id:
                    return r
        return None

    # ----- statistics -----
    def statistics(self) -> Dict[str, Any]:
        """Thống kê tổng hợp."""
        return {
            "rules": len(self._rules.list()),
            "enabled_rules": len(self._rules.enabled_rules()),
            "cameras": len(self._engines),
            "events": self._events.statistics(),
            "alert_queue": {
                "pending": self._alert_queue.size,
                "total_pushed": self._alert_queue.total_pushed,
            },
            "engines": [e.statistics() for e in self._engines.values()],
        }

    def shutdown(self) -> None:
        """Dọn dẹp state."""
        for engine in self._engines.values():
            engine.clear()
        self._engines.clear()
        self._events.clear()
        self._alert_queue.clear()
        logger.info("RuleService shutdown.")
