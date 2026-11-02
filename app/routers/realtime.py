"""Public WebSocket endpoint for the local real-time classroom demonstration."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import ConnectionManager

router = APIRouter(tags=["Real-time"])
manager = ConnectionManager()


@router.websocket("/ws/messages")
async def websocket_messages(websocket: WebSocket) -> None:
    """Broadcast each received text message as JSON to connected clients."""
    await manager.connect(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast(
                {"type": "message", "message": text}, sender=websocket
            )
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
