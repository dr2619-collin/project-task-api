"""Small, deterministic I/O simulations for the Module 09 course demo."""

import asyncio
import time

from app.schemas.async_demo import WaitResponse


class AsyncDemoService:
    """Provide matching synchronous and asynchronous simulated I/O waits."""

    @staticmethod
    def wait_synchronously(seconds: float) -> WaitResponse:
        """Block one thread while simulating a slow synchronous I/O operation."""
        # `time.sleep` stands in for a synchronous client library that waits for
        # a database, file system, or remote service response.
        time.sleep(seconds)
        return WaitResponse(
            mode="sync",
            waited_seconds=seconds,
            message="Completed simulated synchronous I/O wait",
        )

    @staticmethod
    async def wait_asynchronously(seconds: float) -> WaitResponse:
        """Yield to the event loop while simulating a slow async I/O operation."""
        # `await asyncio.sleep` stands in for an awaitable I/O operation. While
        # this coroutine waits, the event loop can run other ready coroutines.
        await asyncio.sleep(seconds)
        return WaitResponse(
            mode="async",
            waited_seconds=seconds,
            message="Completed simulated asynchronous I/O wait",
        )
