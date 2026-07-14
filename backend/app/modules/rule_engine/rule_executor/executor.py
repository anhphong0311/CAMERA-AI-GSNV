"""
RuleExecutor — đánh giá một rule trên facts + cập nhật bộ đếm thời gian (state).

Pipeline: base condition (bỏ leaf duration) → cập nhật timer → điều kiện đầy đủ
(kèm duration) → fired. KHÔNG tạo event ở đây (tách trách nhiệm).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from loguru import logger

from app.modules.rule_engine.exceptions import ExpressionError, RuleEngineException
from app.modules.rule_engine.rule_parser.rule import Rule
from app.modules.rule_engine.state.rule_state import RuleState


def _duration_threshold(rule: Rule) -> float:
    """Lấy ngưỡng duration (giây) từ cây điều kiện rule."""
    from app.modules.rule_engine.condition.nodes import DURATION_TYPE, LeafCondition

    def walk(node) -> Optional[float]:
        if isinstance(node, LeafCondition) and node.type == DURATION_TYPE:
            try:
                return float(node.value)
            except (TypeError, ValueError):
                return None
        children = getattr(node, "conditions", None)
        if children:
            for c in children:
                v = walk(c)
                if v is not None:
                    return v
        return None

    return walk(rule.condition) or 0.0


@dataclass
class ExecutionResult:
    """Kết quả chạy một rule cho một track."""

    base_active: bool
    fired: bool
    active_seconds: float


class RuleExecutor:
    """Đánh giá rule + duy trì timer điều kiện nền."""

    def execute(
        self,
        rule: Rule,
        facts: dict[str, Any],
        state: RuleState,
        now: datetime,
        dt: float,
        gap_reset_seconds: Optional[float] = None,
        frame_index: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Chạy rule.

        Args:
            rule: Rule.
            facts: dict facts.
            state: RuleState của (rule, track).
            now: thời điểm frame.
            dt: giây trôi qua kể từ frame trước của track này.
            gap_reset_seconds: Cho phép mất tín hiệu ngắn (phone timer).
            frame_index: Index frame khi bắt đầu theo dõi.

        Returns:
            ExecutionResult.
        """
        try:
            base_active = rule.condition.evaluate(facts, duration_seconds=None)
        except ExpressionError as exc:
            logger.warning("Rule {} lỗi biểu thức: {}", rule.id, exc.message)
            state.reset_activity()
            state.updated_ts = now
            return ExecutionResult(False, False, 0.0)
        except RuleEngineException as exc:
            logger.warning("Rule {} lỗi: {}", rule.id, exc.message)
            state.reset_activity()
            state.updated_ts = now
            return ExecutionResult(False, False, 0.0)

        if base_active:
            state.gap_seconds = 0.0
            if state.active_since is None:
                state.active_since = now
                state.active_seconds = 0.0
                state.confirm_frames = 1
                state.lifecycle = "ACTIVE"
                if frame_index is not None:
                    state.start_frame_index = frame_index
            else:
                state.active_seconds += max(0.0, dt)
                state.confirm_frames += 1
                state.lifecycle = "ACTIVE"
        elif (
            gap_reset_seconds is not None
            and gap_reset_seconds > 0
            and state.active_since is not None
        ):
            state.gap_seconds += max(0.0, dt)
            if state.gap_seconds <= gap_reset_seconds:
                state.active_seconds += max(0.0, dt)
            else:
                if state.lifecycle == "ACTIVE":
                    state.lifecycle = "CANCELLED"
                    logger.debug(
                        "Timer reset rule={} track={} gap={:.1f}s",
                        rule.id,
                        state.track_id,
                        state.gap_seconds,
                    )
                state.reset_activity()
        else:
            if state.active_since is not None and state.lifecycle == "ACTIVE":
                state.lifecycle = "CANCELLED"
            state.reset_activity()

        in_grace = (
            not base_active
            and gap_reset_seconds is not None
            and gap_reset_seconds > 0
            and state.active_since is not None
            and 0 < state.gap_seconds <= gap_reset_seconds
        )

        if base_active:
            fired = rule.condition.evaluate(
                facts, duration_seconds=state.active_seconds
            )
        elif in_grace:
            fired = rule.condition.duration_satisfied(state.active_seconds)
        else:
            fired = False

        if fired and state.evidence_time is None:
            from datetime import timedelta

            if rule.id == "AWAY_FROM_DESK":
                # Snapshot lúc xác nhận vắng mặt (= bàn trống), không phải lúc vừa rời
                state.evidence_time = now
            elif rule.id == "PHONE_USAGE":
                # Snapshot lúc xác nhận đang dùng điện thoại
                state.evidence_time = now
            else:
                threshold = _duration_threshold(rule)
                state.evidence_time = (state.active_since or now) + timedelta(
                    seconds=threshold
                )

        state.last_ts = now
        state.updated_ts = now
        return ExecutionResult(base_active, fired, state.active_seconds)
