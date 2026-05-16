import asyncio
import json
from typing import Any
from fastapi import WebSocket


class WebSocketManager:
    """
    Gestiona conexiones WebSocket para el dashboard en tiempo real.
    Permite broadcast de actualizaciones a todos los clientes conectados.
    """

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]):
        async with self._lock:
            disconnected = []
            for ws in self._connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)

            for ws in disconnected:
                if ws in self._connections:
                    self._connections.remove(ws)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def send_provider_update(self, providers: list[dict]):
        await self.broadcast({
            "type": "providers_update",
            "data": providers,
        })

    async def send_request_update(self, request_id: str, status: str):
        await self.broadcast({
            "type": "request_update",
            "data": {"request_id": request_id, "status": status},
        })

    async def send_health_update(self, health: dict):
        await self.broadcast({
            "type": "health_update",
            "data": health,
        })

    async def send_auction_update(self, auction: dict):
        await self.broadcast({
            "type": "auction_update",
            "data": auction,
        })


ws_manager = WebSocketManager()
