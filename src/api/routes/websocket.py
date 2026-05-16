from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.websocket_manager import ws_manager
from core.cache import response_cache

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket para actualizaciones en tiempo real del dashboard.
    Envía updates de providers, requests, health y auctions.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "get_cache_stats":
                await websocket.send_json({
                    "type": "cache_stats",
                    "data": response_cache.get_stats(),
                })
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    return {
        "active_connections": ws_manager.active_connections,
        "cache_stats": response_cache.get_stats(),
    }
