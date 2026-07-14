"""
Bridge Detection → Tracking → Behavior → Realtime overlay / Rule alerts.

Chạy trong callback pipeline AI (worker thread) — không block camera loop.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
from loguru import logger

from app.modules.ai.models import DetectionResult
from app.modules.performance.config.loader import PipelineConfig, load_performance_config
from app.modules.realtime.broadcaster import RealtimeBroadcaster
from app.modules.realtime.detection_serializer import detection_result_to_dashboard


class RealtimePipelineBridge:
    """Xử lý hậu kỳ sau mỗi DetectionResult và đẩy lên WebSocket."""

    def __init__(
        self,
        app,
        broadcaster: RealtimeBroadcaster,
        pipeline_config: Optional[PipelineConfig] = None,
    ) -> None:
        self._app = app
        self._broadcaster = broadcaster
        cfg = pipeline_config or load_performance_config().pipeline
        self._chain_tracking = cfg.chain_tracking
        self._chain_behavior = cfg.chain_behavior
        self._chain_rules = cfg.chain_rules
        self._behavior_tick: dict[int, int] = {}

    def handle(self, result: DetectionResult) -> None:
        frame = self._latest_frame(result.camera_id)
        # Evidence frames đã được camera frame_sink đẩy vào EventService
        # (wire_evidence_frame_sink) — không push trùng tại AI FPS.

        tracking = None
        behavior = None

        if self._chain_tracking or self._chain_behavior or self._chain_rules:
            tracking_svc = getattr(self._app.state, "tracking_service", None)
            if tracking_svc is not None:
                tracking = tracking_svc.process(result)

        # Chạy behavior mỗi frame detection — trước đây chỉ mỗi 3 frame nên
        # PHONE_USAGE gần như không bao giờ đủ duration liên tục.
        if self._chain_behavior and tracking is not None and frame is not None:
            behavior_svc = getattr(self._app.state, "behavior_service", None)
            if behavior_svc is not None:
                try:
                    behavior = behavior_svc.process(
                        frame, tracking, detections=result.objects
                    )
                except Exception as exc:
                    logger.warning(
                        "Behavior chain skipped cam={}: {}", result.camera_id, exc
                    )

        if self._chain_rules and tracking is not None and behavior is not None:
            rule_svc = getattr(self._app.state, "rule_service", None)
            if rule_svc is not None:
                try:
                    events = rule_svc.process(result, tracking, behavior)
                    for ev in events:
                        self._broadcaster.publish_alert_from_event(ev)
                        logger.info(
                            "Rule alert queued rule={} cam={} track={}",
                            ev.rule_id,
                            ev.camera_id,
                            ev.track_id,
                        )
                except Exception as exc:
                    logger.warning(
                        "Rule chain skipped cam={}: {}", result.camera_id, exc
                    )

        payload = detection_result_to_dashboard(
            result, tracking=tracking, behavior=behavior
        )
        self._broadcaster.publish_detection_payload(payload)

    def _latest_frame(self, camera_id: int) -> Optional[np.ndarray]:
        manager = getattr(self._app.state, "camera_manager", None)
        if manager is None:
            return None
        workers = getattr(manager, "_workers", {})
        worker = workers.get(camera_id)
        if worker is None:
            return None
        buf = getattr(worker, "frame_buffer", None)
        if buf is None:
            return None
        packet = buf.latest()
        return packet.data if packet is not None else None


def create_detection_sink(app, broadcaster: RealtimeBroadcaster):
    """Factory callback cho DetectionService.set_detection_sink."""
    bridge = RealtimePipelineBridge(app, broadcaster)
    return bridge.handle
