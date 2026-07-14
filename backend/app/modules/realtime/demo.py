"""
Demo realtime generator — sinh dữ liệu detection/tracking/alert giả lập.

Dùng khi chưa có luồng camera thật để Dashboard demo được realtime end-to-end.
Bật/tắt qua env AEMS_REALTIME_DEMO (mặc định bật).
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List

_OBJECTS = ["person", "phone", "cup", "bottle", "food", "laptop", "monitor", "keyboard"]
_RULES = ["PHONE_USAGE", "AWAY_FROM_DESK", "PRIVATE_TALKING", "EATING", "SLEEPING", "IDLE"]
_ROIS = ["Desk 01", "Desk 05", "Meeting", "Corridor", "Entrance"]
_SEVERITY = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


class DemoStream:
    """Trạng thái demo cho một số camera ảo."""

    def __init__(self, cameras: int = 4) -> None:
        self._cameras = list(range(1, cameras + 1))
        self._tracks: Dict[int, Dict[int, Dict[str, Any]]] = {
            cid: {} for cid in self._cameras
        }
        self._next_track = 1

    def cameras(self) -> List[int]:
        return list(self._cameras)

    def _ensure_tracks(self, camera_id: int) -> None:
        tracks = self._tracks[camera_id]
        if len(tracks) < random.randint(1, 3):
            tid = self._next_track
            self._next_track += 1
            tracks[tid] = {
                "x": random.uniform(0.1, 0.7),
                "y": random.uniform(0.1, 0.7),
                "roi": random.choice(_ROIS),
                "duration": 0.0,
                "stationary": 0.0,
            }
        # đôi khi xoá track
        if tracks and random.random() < 0.1:
            tracks.pop(random.choice(list(tracks.keys())))

    def detection_frame(self, camera_id: int) -> Dict[str, Any]:
        """Sinh detection cho một camera."""
        self._ensure_tracks(camera_id)
        objs = []
        for tid, st in self._tracks[camera_id].items():
            st["x"] = min(0.85, max(0.02, st["x"] + random.uniform(-0.03, 0.03)))
            st["y"] = min(0.85, max(0.02, st["y"] + random.uniform(-0.03, 0.03)))
            objs.append(
                {
                    "track_id": tid,
                    "label": "person",
                    "confidence": round(random.uniform(0.7, 0.99), 2),
                    "bbox": [round(st["x"], 3), round(st["y"], 3), 0.12, 0.28],
                    "roi": st["roi"],
                }
            )
            if random.random() < 0.35:
                objs.append(
                    {
                        "track_id": None,
                        "label": random.choice(_OBJECTS[1:]),
                        "confidence": round(random.uniform(0.5, 0.95), 2),
                        "bbox": [
                            round(st["x"] + 0.05, 3),
                            round(st["y"] + 0.05, 3),
                            0.05,
                            0.05,
                        ],
                        "roi": st["roi"],
                    }
                )
        return {
            "camera_id": camera_id,
            "fps": round(random.uniform(22, 30), 1),
            "objects": objs,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    def tracking_frame(self, camera_id: int) -> Dict[str, Any]:
        """Sinh tracking info cho một camera."""
        tracks = []
        for tid, st in self._tracks[camera_id].items():
            st["duration"] += random.uniform(0.5, 1.5)
            speed = round(random.uniform(0, 2.5), 2)
            st["stationary"] = st["stationary"] + 1 if speed < 0.3 else 0.0
            tracks.append(
                {
                    "track_id": tid,
                    "camera_id": camera_id,
                    "roi": st["roi"],
                    "duration": round(st["duration"], 1),
                    "speed": speed,
                    "direction": random.choice(
                        ["UP", "DOWN", "LEFT", "RIGHT", "STATIONARY"]
                    ),
                    "stationary_time": round(st["stationary"], 1),
                }
            )
        return {
            "camera_id": camera_id,
            "tracks": tracks,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    def maybe_alert(self) -> Dict[str, Any] | None:
        """Thỉnh thoảng sinh một alert."""
        if random.random() > 0.25:
            return None
        camera_id = random.choice(self._cameras)
        tracks = self._tracks[camera_id]
        track_id = random.choice(list(tracks.keys())) if tracks else 0
        rule = random.choice(_RULES)
        return {
            "event_id": f"demo-{random.randint(100000, 999999)}",
            "camera_id": camera_id,
            "camera_name": f"Office {camera_id:02d}",
            "track_id": track_id,
            "rule_id": rule,
            "severity": random.choice(_SEVERITY),
            "confidence": round(random.uniform(0.6, 0.99), 2),
            "duration": round(random.uniform(5, 60), 1),
            "roi": random.choice(_ROIS),
            "status": "NEW",
            "ts": datetime.now(timezone.utc).isoformat(),
        }
