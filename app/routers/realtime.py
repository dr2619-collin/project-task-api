"""Public WebSocket endpoint for the local real-time classroom demonstration."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import ConnectionManager

router = APIRouter(tags=["Real-time"])
manager = ConnectionManager()


@router.websocket("/ws/messages")
async def websocket_messages(websocket: WebSocket) -> None:
    """Broadcast each received text message as JSON to connected clients."""
    # This handler runs once per client connection. Wait for the handshake to
    # finish and the connection to be registered before receiving messages.
    await manager.connect(websocket)
    try:
        while True:
            # Wait for the next text message from this client.
            text = await websocket.receive_text()
            # Send it to the other connected clients; the sender is excluded.
            await manager.broadcast(
                {"type": "message", "message": text}, sender=websocket
            )
    except WebSocketDisconnect:
        # A normal client disconnect ends this connection's receive loop.
        pass
    finally:
        # Remove this client whether the loop ended normally or with an error.
        manager.disconnect(websocket)
