"""WebSocket broadcast manager for real-time data."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class BroadcastManager:
    """Manages WebSocket clients and broadcasts readings."""

    def __init__(self):
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._latest: dict[str, Any] = {}

    async def add_client(self, ws: WebSocket):
        async with self._lock:
            self._clients.add(ws)
            logger.info(f"WebSocket client connected. Total: {len(self._clients)}")

    async def remove_client(self, ws: WebSocket):
        async with self._lock:
            self._clients.discard(ws)
            logger.info(f"WebSocket client disconnected. Total: {len(self._clients)}")

    @property
    def client_count(self) -> int:
        return len(self._clients)

    @property
    def latest_readings(self) -> dict[str, Any]:
        return self._latest.copy()

    async def broadcast(
        self,
        readings: dict[str, Any],
        connected: bool,
        device_id: str | None = None,
        measurement_id: str | None = None,
    ):
        """Send readings to all connected WebSocket clients."""
        self._latest = readings

        if not self._clients:
            return

        message = json.dumps(
            {
                "type": "readings",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "connected": connected,
                "device_id": device_id,
                "measurement_id": measurement_id,
                "data": readings,
            },
            default=str,
        )

        dead_clients: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:
                dead_clients.append(ws)

        if dead_clients:
            async with self._lock:
                for ws in dead_clients:
                    self._clients.discard(ws)

    async def broadcast_status(self, status: str, message: str = ""):
        """Send a status message to all clients."""
        if not self._clients:
            return

        msg = json.dumps(
            {
                "type": "status",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": status,
                "message": message,
            }
        )

        dead_clients: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(msg)
            except Exception:
                dead_clients.append(ws)

        if dead_clients:
            async with self._lock:
                for ws in dead_clients:
                    self._clients.discard(ws)
