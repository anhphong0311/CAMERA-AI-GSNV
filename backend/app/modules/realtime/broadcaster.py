"""
RealtimeBroadcaster — vòng lặp nền phát dữ liệu realtime tới Dashboard.

Giữ buffer alert gần đây + snapshot system + trạng thái camera để REST API
(overview / alerts / system) đọc được ngay cả khi chưa có camera thật.
"""

from __future__ import annotations

import asyncio
import os
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List, Optional

from loguru import logger

from app.modules.ai.models import DetectionResult
from app.modules.realtime.demo import DemoStream
from app.modules.realtime.detection_serializer import detection_result_to_dashboard
from app.modules.realtime.hub import ConnectionManager
from app.modules.realtime.metrics import collect_system_metrics


def _demo_enabled() -> bool:
    return os.getenv("AEMS_REALTIME_DEMO", "true").lower() in ("1", "true", "yes")


class RealtimeBroadcaster:
    """Phát realtime + lưu snapshot gần nhất cho REST."""

    def __init__(self, manager: ConnectionManager, interval: float = 1.0) -> None:
        self._manager = manager
        self._interval = interval
        self._demo = DemoStream(cameras=4) if _demo_enabled() else None
        self._task: Optional[asyncio.Task] = None
        self._recent_alerts: Deque[Dict[str, Any]] = deque(maxlen=200)
        self._latest_system: Dict[str, Any] = {}
        self._latest_detection: Dict[int, Dict[str, Any]] = {}
        self._latest_tracking: Dict[int, Dict[str, Any]] = {}
        self._today_alerts = 0
        self._start_day = datetime.now(timezone.utc).date()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._fetch_cameras: Optional[
            Callable[[], Any]
        ] = None  # async () -> list[dict]
        self._live_camera_cache: List[Dict[str, Any]] = []

    def set_camera_fetcher(self, fetcher: Callable[[], Any]) -> None:
        """Async fetcher trả danh sách camera từ DB."""
        self._fetch_cameras = fetcher

    def publish_detection_from_result(self, result: DetectionResult) -> None:
        """Gọi từ worker thread AI — đẩy detection thật lên WebSocket (legacy)."""
        payload = detection_result_to_dashboard(result)
        self.publish_detection_payload(payload)

    def publish_detection_payload(self, payload: Dict[str, Any]) -> None:
        """Lưu snapshot + broadcast detection frame."""
        cam_id = payload.get("camera_id")
        if cam_id is not None:
            self._latest_detection[int(cam_id)] = payload
        self._publish_detection_async(payload)

    def publish_alert_from_event(self, event) -> None:
        """Đẩy alert thật từ Rule Engine lên WebSocket."""
        alert = {
            "event_id": event.event_id,
            "camera_id": event.camera_id,
            "camera_name": f"Camera {event.camera_id}",
            "track_id": event.track_id,
            "rule_id": event.rule_id,
            "severity": getattr(event.severity, "value", str(event.severity)),
            "confidence": round(float(event.confidence), 2),
            "duration": round(float(event.duration), 1),
            "roi": event.metadata.get("roi") if event.metadata else None,
            "status": getattr(event.state, "value", str(event.state)),
            "ts": event.start_time.isoformat(),
        }
        self._recent_alerts.appendleft(alert)
        self._today_alerts += 1
        if self._loop is None or self._loop.is_closed():
            return
        asyncio.run_coroutine_threadsafe(
            self._manager.broadcast({"channel": "alert", "data": alert}),
            self._loop,
        )

    def _publish_detection_async(self, payload: Dict[str, Any]) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        asyncio.run_coroutine_threadsafe(
            self._manager.broadcast({"channel": "detection", "data": payload}),
            self._loop,
        )

    def start(self) -> None:
        """Khởi động vòng lặp nền."""
        if self._task is None:
            self._loop = asyncio.get_running_loop()
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Dừng vòng lặp."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

    async def _run_loop(self) -> None:
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover
                logger.warning("Broadcaster tick lỗi: {}", exc)
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc)
        if now.date() != self._start_day:
            self._today_alerts = 0
            self._start_day = now.date()

        # System metrics (chạy trong thread để psutil không block loop)
        system = await asyncio.to_thread(collect_system_metrics)
        self._latest_system = system
        await self._manager.broadcast({"channel": "system", "data": system})

        if self._demo is None:
            if self._fetch_cameras is not None:
                try:
                    rows = await self._fetch_cameras()
                    self._live_camera_cache = [
                        {
                            **row,
                            "fps": self._latest_detection.get(
                                row["camera_id"], {}
                            ).get("fps", row.get("fps", 0)),
                        }
                        for row in rows
                    ]
                except Exception as exc:
                    logger.debug("Camera status fetch skipped: {}", exc)
            return

        for cam in self._demo.cameras():
            det = self._demo.detection_frame(cam)
            self._latest_detection[cam] = det
            await self._manager.broadcast({"channel": "detection", "data": det})

            trk = self._demo.tracking_frame(cam)
            self._latest_tracking[cam] = trk
            await self._manager.broadcast({"channel": "tracking", "data": trk})

        alert = self._demo.maybe_alert()
        if alert is not None:
            self._recent_alerts.appendleft(alert)
            self._today_alerts += 1
            await self._manager.broadcast({"channel": "alert", "data": alert})

    # ----- REST read models -----
    def recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self._recent_alerts)[:limit]

    def latest_system(self) -> Dict[str, Any]:
        return self._latest_system or collect_system_metrics()

    def camera_status(self) -> List[Dict[str, Any]]:
        if self._demo is not None:
            cams = self._demo.cameras()
            return [
                {
                    "camera_id": c,
                    "name": f"Office {c:02d}",
                    "status": "online",
                    "fps": self._latest_detection.get(c, {}).get("fps", 0),
                }
                for c in cams
            ]
        if self._live_camera_cache:
            return self._live_camera_cache
        return []

    def overview(self) -> Dict[str, Any]:
        cams = self.camera_status()
        online = sum(1 for c in cams if c["status"] == "online")
        avg_fps = round(
            sum(c["fps"] for c in cams) / len(cams), 1
        ) if cams else 0.0
        return {
            "cameras_online": online,
            "cameras_offline": len(cams) - online,
            "cameras_total": len(cams),
            "ai_fps": avg_fps,
            "today_alerts": self._today_alerts,
            "today_violations": self._today_alerts,
            "system": self.latest_system(),
        }
