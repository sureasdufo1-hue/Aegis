import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("soc.dashboard.ws")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {
            "events": set(),
            "traffic": set(),
            "alerts": set(),
            "incidents": set(),
            "system": set(),
            "stream": set(),
        }

    async def connect(self, websocket: WebSocket, channel: str = "stream"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket client connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str = "stream"):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
        logger.info(f"WebSocket client disconnected from channel: {channel}")

    async def broadcast(self, message: dict[str, Any], channel: str = "stream"):
        targets = list(self.active_connections.get(channel, set()))
        if not targets:
            return
        payload = json.dumps(message, ensure_ascii=False)
        disconnected = []
        for connection in targets:
            try:
                await connection.send_text(payload)
            except (WebSocketDisconnect, RuntimeError, OSError):
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn, channel)

    async def broadcast_all(self, message: dict[str, Any]):
        for channel in list(self.active_connections.keys()):
            await self.broadcast(message, channel)


ws_manager = ConnectionManager()
