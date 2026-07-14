"""
ConnectionManager — quản lý các WebSocket client của Dashboard.

Thread-safe qua asyncio.Lock; broadcast JSON tới mọi client, tự loại client chết.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Set

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """Quản lý kết nối WebSocket + broadcast."""

    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._total_connected = 0

    async def connect(self, ws: WebSocket) -> None:
        """Chấp nhận và đăng ký client."""
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
            self._total_connected += 1
        logger.info("WS client connected (active={})", len(self._clients))

    async def disconnect(self, ws: WebSocket) -> None:
        """Gỡ client."""
        async with self._lock:
            self._clients.discard(ws)
        logger.info("WS client disconnected (active={})", len(self._clients))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Gửi một message JSON tới tất cả client (bỏ client lỗi)."""
        async with self._lock:
            targets: List[WebSocket] = list(self._clients)
        dead: List[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)

    async def send_personal(self, ws: WebSocket, message: Dict[str, Any]) -> None:
        """Gửi message tới một client cụ thể."""
        try:
            await ws.send_json(message)
        except Exception:
            await self.disconnect(ws)

    @property
    def active(self) -> int:
        """Số client đang kết nối."""
        return len(self._clients)

    @property
    def total_connected(self) -> int:
        return self._total_connected
