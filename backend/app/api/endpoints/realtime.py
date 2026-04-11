"""WebSocket endpoint for real-time data streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..deps import get_broadcast

router = APIRouter()


@router.websocket("/ws/realtime")
async def realtime_ws(websocket: WebSocket):
    """WebSocket endpoint that streams live PM8000 readings.

    Messages are pushed by the collector every poll cycle (~1s).
    Format: {"type": "readings", "timestamp": "...", "connected": true, "data": {...}}
    """
    await websocket.accept()
    broadcast = get_broadcast()
    await broadcast.add_client(websocket)

    try:
        # Keep connection alive - wait for client messages (ping/pong)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await broadcast.remove_client(websocket)
