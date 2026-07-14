"""
Watchdog (Sprint 11) — theo dõi Backend/Worker/Camera/Redis/DB/GPU, gửi cảnh báo Telegram.

Chạy độc lập: `python -m app.modules.ops.watchdog` hoặc container systemd.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class Watchdog:
    """Poll health endpoints và phát cảnh báo khi component lỗi."""

    def __init__(
        self,
        backend_url: str = "http://backend:8000",
        interval_s: float = 30.0,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ) -> None:
        self._url = backend_url.rstrip("/")
        self._interval = interval_s
        self._token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self._last_alerts: Dict[str, float] = {}
        self._cooldown_s = 300.0

    async def check_once(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(f"{self._url}/api/v1/health/full")
                data = resp.json().get("data", {})
            except Exception as exc:
                data = {"status": "unhealthy", "error": str(exc), "components": {}}
                await self._maybe_alert("backend", f"Backend unreachable: {exc}")
                return data

        status = data.get("status", "unknown")
        if status != "healthy":
            await self._maybe_alert("health", f"System status: {status}")
        for name, comp in (data.get("components") or {}).items():
            if isinstance(comp, dict) and comp.get("ok") is False:
                await self._maybe_alert(name, f"{name} unhealthy: {comp.get('detail', comp)}")
        return data

    async def _maybe_alert(self, key: str, message: str) -> None:
        now = time.time()
        if now - self._last_alerts.get(key, 0) < self._cooldown_s:
            return
        self._last_alerts[key] = now
        logger.warning("WATCHDOG ALERT [{}]: {}", key, message)
        if self._token and self._chat_id:
            try:
                url = f"https://api.telegram.org/bot{self._token}/sendMessage"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(url, json={"chat_id": self._chat_id, "text": f"🚨 AEMS Watchdog\n{message}"})
            except Exception as exc:
                logger.error("Telegram alert failed: {}", exc)

    async def run_forever(self) -> None:
        logger.info("Watchdog started | url={} interval={}s", self._url, self._interval)
        while True:
            await self.check_once()
            await asyncio.sleep(self._interval)


def main() -> None:
    url = os.getenv("WATCHDOG_BACKEND_URL", "http://127.0.0.1:8000")
    interval = float(os.getenv("WATCHDOG_INTERVAL_S", "30"))
    wd = Watchdog(backend_url=url, interval_s=interval)
    try:
        asyncio.run(wd.run_forever())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
