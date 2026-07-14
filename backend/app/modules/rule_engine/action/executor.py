"""
ActionExecutor — thực thi actions của rule khi event được xác nhận.

Hành động hỗ trợ: "alert" (đẩy AlertQueue), "log". KHÔNG Telegram/DB/Dashboard.
"""

from __future__ import annotations

from typing import Iterable

from loguru import logger

from app.modules.rule_engine.action.alert_queue import AlertQueue
from app.modules.rule_engine.event.event import BehaviorEventDTO


class ActionExecutor:
    """Điều phối hành động của rule trên một event."""

    def __init__(self, alert_queue: AlertQueue) -> None:
        self._alert_queue = alert_queue

    def execute(self, actions: Iterable[str], event: BehaviorEventDTO) -> None:
        """Chạy danh sách action cho event."""
        for action in actions:
            name = action.lower()
            if name == "alert":
                self._alert_queue.push(event)
                logger.debug(
                    "Action alert → queue | rule={} track={}",
                    event.rule_id,
                    event.track_id,
                )
            elif name == "log":
                logger.info(
                    "Behavior event: {} track={} severity={}",
                    event.rule_id,
                    event.track_id,
                    event.severity.value,
                )
            else:
                logger.warning("Action không hỗ trợ: {}", action)
