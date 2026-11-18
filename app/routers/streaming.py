"""Standalone HTTP streaming demonstration endpoint."""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["Streaming"])


async def demonstration_events() -> AsyncIterator[str]:
    """Yield a finite sequence of sample Server-Sent Event-style frames."""
    for sequence in range(1, 4):
        payload = json.dumps(
            {"sequence": sequence, "message": "Demonstration update"}
        )
        yield f"event: update\ndata: {payload}\n\n"
        if sequence < 3:
            await asyncio.sleep(0.25)


@router.get(
    "/stream",
    summary="Stream demonstration events",
    description="Send a finite sequence of sample events over HTTP.",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "A finite Server-Sent Event-style demonstration stream.",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        },
    },
)
async def stream_demo() -> Response:
    """Return a finite teaching stream without accessing Project data."""
    return StreamingResponse(demonstration_events(), media_type="text/event-stream")
