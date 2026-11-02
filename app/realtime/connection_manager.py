"""Manage active WebSocket connections for the local course demonstration."""

from fastapi import WebSocket


class ConnectionManager:
    """Track and broadcast to WebSockets connected to one API process."""

    def __init__(self) -> None:
        # These are temporary connection objects, not durable business data.
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and remember a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Forget a connection when its client disconnects."""
        self.active_connections.discard(websocket)

    async def broadcast(
        self, message: dict[str, str], *, sender: WebSocket
    ) -> None:
        """Send one JSON message to every connected client except its sender."""
        # Iterate over a snapshot so connection changes do not mutate this loop.
        for connection in tuple(self.active_connections):
            if connection is not sender:
                await connection.send_json(message)
