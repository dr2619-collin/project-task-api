# Module 09 — Async I/O and Concurrency Limits

Module 09 compares two ways an API can wait for I/O: a normal synchronous route
that blocks a thread and an asynchronous route that yields to the event loop.
The purpose is not to make every route `async`, but to select the design that
matches the libraries and work a route performs.

## Match the route style to its I/O

A normal `def` route is appropriate when it calls synchronous code. FastAPI
runs that route in its shared threadpool, so a blocking call such as
`time.sleep()` does not block the event-loop thread.

An `async def` route is appropriate only when its slow operation is awaitable:

```python
async def wait_asynchronously(seconds: float) -> WaitResponse:
    await asyncio.sleep(seconds)
```

At `await`, the coroutine pauses and the event loop can run other ready
coroutines. Async does not make the external operation itself faster; it lets
other requests make progress while this request waits.

The two Module 09 routes are deliberately small, deterministic demonstrations:

- [`app/routers/async_demo.py`](../../app/routers/async_demo.py) exposes public
  synchronous and asynchronous wait endpoints.
- [`app/services/async_demo.py`](../../app/services/async_demo.py) uses
  `time.sleep()` and `asyncio.sleep()` as stand-ins for slow I/O.

Do not put a blocking call inside `async def`. A synchronous HTTP client,
synchronous database driver, or `time.sleep()` in an async route blocks the
event loop and prevents other async requests from progressing.

## Configure the threadpool limit

The threadpool has limited capacity. A blocking synchronous request occupies a
thread until its operation finishes; additional requests wait for a thread to
be available. Module 09 uses `SYNC_THREADPOOL_SIZE` to make that queue visible
during the classroom demonstration.

Configuration belongs in the typed `Settings` class, not in individual routers
or services. `Settings` reads the environment at startup, validates that
`SYNC_THREADPOOL_SIZE` is at least one, and supplies the resulting value to the
application lifespan. The lifespan then configures AnyIO's shared thread
limiter before serving requests.

This keeps configuration behavior in one place:

- Components receive already-validated settings instead of rereading the
  environment.
- The default value of 40 is documented in code.
- Invalid configuration fails clearly during startup.
- The demonstration can use a smaller value without changing application code.

## Know which resource is limiting throughput

Different work is constrained by different resources:

| Work | Main limit | Effect when exhausted |
|---|---|---|
| Synchronous route work | AnyIO threadpool | Later synchronous requests wait for a worker thread. |
| Awaitable I/O | Event loop and the remote system | Many coroutines can wait without one thread per request. |
| PostgreSQL work | Database connection pool | Requests wait for an available database connection. |
| CPU-heavy work | CPU cores | The process becomes busy; async does not make computation faster. |

Increasing one limit does not remove another. For example, increasing the
threadpool beyond the database connection pool creates more requests waiting
for database connections; it does not create more concurrent database queries.

## Preserve synchronous persistence boundaries

The Project and Task routes remain synchronous because this application uses a
synchronous SQLAlchemy `Session` and PostgreSQL driver. Rewriting only a router
as `async def` would not make its database calls awaitable and could place
blocking work on the event-loop path.

A complete async database design requires coordinated changes: an async engine,
`AsyncSession`, an asyncio-compatible driver, and awaited repository, service,
and router calls. That is a deliberate architecture change, not a keyword-only
conversion.

For the runnable comparison and k6 results, see [Async I/O](../async-io.md).
