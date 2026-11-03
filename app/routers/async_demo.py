"""Public endpoints that compare synchronous and asynchronous I/O waiting."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.async_demo import WaitResponse
from app.services.async_demo import AsyncDemoService

router = APIRouter(prefix="/async-demo", tags=["Async I/O"])

# FastAPI reads this value from the `seconds` URL query string, converts it to
# a float, and validates it. The small upper limit keeps local classroom
# demonstrations responsive while still making concurrent waits observable.
WaitSeconds = Annotated[
    float,
    Query(
        ge=0,
        le=3,
        description="Seconds to wait while simulating a slow I/O operation.",
    ),
]


@router.get(
    "/sync-wait",
    response_model=WaitResponse,
    summary="Wait with a synchronous route",
    description=(
        "Simulate blocking I/O in a normal def route. FastAPI runs this route "
        "in its threadpool."
    ),
)
def wait_synchronously(seconds: WaitSeconds = 1.0) -> WaitResponse:
    """Return after a blocking synchronous wait completes."""
    return AsyncDemoService.wait_synchronously(seconds)


@router.get(
    "/async-wait",
    response_model=WaitResponse,
    summary="Wait with an asynchronous route",
    description=(
        "Simulate awaitable I/O in an async def route. The coroutine yields "
        "control to the event loop while it waits."
    ),
)
async def wait_asynchronously(seconds: WaitSeconds = 1.0) -> WaitResponse:
    """Return after an awaitable asynchronous wait completes."""
    return await AsyncDemoService.wait_asynchronously(seconds)
