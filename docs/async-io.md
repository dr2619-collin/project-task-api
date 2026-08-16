# Async I/O

## Compare sync vs. async I/O

Module 09 compares two public routes that simulate waiting for a slow external dependency. The simulated wait is not useful application work; it stands in for time spent waiting for a remote HTTP API, file system, cloud service, or an async-compatible database driver.

| Route | Implementation | What the demo shows |
|---|---|---|
| `GET /async-demo/sync-wait?seconds=0.25` | A normal `def` route with `time.sleep()` | FastAPI places blocking synchronous work in its threadpool. |
| `GET /async-demo/async-wait?seconds=0.25` | An `async def` route with `await asyncio.sleep()` | The coroutine yields to the event loop while it waits. |

Both endpoints are public so the demonstration focuses on concurrency rather than authorization. They accept an optional `seconds` query parameter from `0` through `3`; valid requests return `200 OK`. The simulated `asyncio.sleep()` is a deterministic stand-in for waiting on an external service, file operation, or async-compatible database driver.

The k6 script starts 80 virtual users, each making one request. With the same simulated `0.25`-second (250 ms) wait, async requests can wait together. Synchronous requests use threadpool workers, so requests beyond the configured worker limit wait for an earlier group to finish.

| Scenario | Total requests | Expected groups | Expected completion time | Calculation |
|---|---:|---|---:|---|
| Synchronous route, default 40-thread pool | 80 | `80 / 40 = 2` | 500 ms | `2 × 250 ms` |
| Synchronous route, 10-thread pool | 80 | `80 / 10 = 8` | 2,000 ms | `8 × 250 ms` |
| Asynchronous route | 80 | 1 concurrent group | 250 ms | `1 × 250 ms` |

The completion times are useful expectations for the total run and high-percentile request durations. Actual k6 measurements include local scheduling, startup, and network overhead, so they will be somewhat higher and can vary by machine.

This is a concurrency demonstration, not a production benchmark. The two endpoints use no database and no external network call, so the comparison isolates how the application waits.

## Run the demo

1. Install k6 on macOS with Homebrew:

   ```bash
   brew install k6
   ```

   For Windows, Linux, Docker, and other environments, use the official [Install k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) instructions.

2. Start the API with its default 40-thread synchronous threadpool from the repository root in one terminal:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

3. Optionally open `http://localhost:8000/docs` and call each endpoint once. Both should return `200 OK` with a JSON body that identifies its `mode` and `waited_seconds`.

4. In a second terminal at the repository root, run the synchronous comparison with the default threadpool:

   ```bash
   ENDPOINT=sync-wait k6 run scripts/load/async-demo.js
   ```

5. Stop the API with `Ctrl+C`, then restart it with a 10-thread synchronous threadpool:

   ```bash
   SYNC_THREADPOOL_SIZE=10 uv run uvicorn app.main:app --reload
   ```

   This environment variable applies only to that server process. When it is omitted, the course demo uses its normal default of 40 tokens.

6. Run the synchronous comparison again:

   ```bash
   ENDPOINT=sync-wait k6 run scripts/load/async-demo.js
   ```

7. Without restarting the API, run the async comparison:

   ```bash
   ENDPOINT=async-wait k6 run scripts/load/async-demo.js
   ```

k6 reports request duration, percentile, request-count, and failure information at the end of each run. Do not compare a single laptop's numbers to a universal target; compare the two runs made on the same machine.

## k6 results

Record the `http_req_duration` values from each k6 summary in this comparison table. They represent individual client request durations.

| Scenario | Expected groups | Expected completion time | Actual average request duration | Actual p95 request duration |
|---|---|---:|---:|---:|
| Synchronous route, default 40-thread pool | `80 / 40 = 2` | 500 ms | 530.35 ms | 533.16 ms |
| Synchronous route, 10-thread pool | `80 / 10 = 8` | 2,000 ms | 2,060 ms | 2,060 ms |
| Asynchronous route | 1 concurrent group | 250 ms | 268.03 ms | 269.60 ms |

## Result analysis

All three runs completed 80 successful requests. The timing differences reflect how each route waits:

- With the default 40-thread pool, the synchronous route needed two groups of requests. Its 530.35 ms average and 533.16 ms p95 closely match the 500 ms expectation: two 250 ms blocking waits, plus local overhead.
- With a 10-thread pool, the same synchronous route needed eight groups. Its 2,060 ms average and p95 closely match the 2,000 ms expectation. Each `time.sleep()` held one threadpool worker, so later requests waited for a worker before beginning their simulated I/O.
- The asynchronous route completed with a 268.03 ms average and 269.60 ms p95, close to one 250 ms wait even while the server used the 10-thread synchronous threadpool limit. At `await asyncio.sleep()`, each coroutine yielded to the event loop instead of holding a threadpool worker.

A normal FastAPI `def` route is safe for synchronous I/O because FastAPI sends it to the threadpool, but that pool has finite capacity. An `async def` route with an awaitable I/O operation lets the event-loop thread switch to other ready requests while each coroutine waits. Async does not make the 250 ms wait itself faster; it avoids serializing concurrent waits behind a limited number of blocking worker threads.

## Two route styles

```python
@router.get("/sync-wait")
def wait_synchronously(seconds: float = 1.0) -> WaitResponse:
    return AsyncDemoService.wait_synchronously(seconds)
```

The synchronous service uses `time.sleep(seconds)`. FastAPI runs this normal `def` route in its threadpool, so the blocking wait occupies one threadpool worker rather than blocking the event-loop thread.

```python
@router.get("/async-wait")
async def wait_asynchronously(seconds: float = 1.0) -> WaitResponse:
    return await AsyncDemoService.wait_asynchronously(seconds)
```

The asynchronous service uses `await asyncio.sleep(seconds)`. At `await`, the request coroutine yields control. The event loop can run other ready coroutines until the timer completes.

```text
async def + awaitable I/O
  -> coroutine pauses at await
  -> event loop runs other ready coroutines
  -> coroutine resumes when I/O is ready
```

## What not to do

Do not place a blocking call directly inside `async def`:

```python
async def incorrect_wait(seconds: float) -> None:
    time.sleep(seconds)  # Blocks the event loop.
```

Likewise, do not directly call a synchronous HTTP or database client inside an async route. Use a compatible awaitable library or keep the route synchronous.

## Why Project and Task CRUD remains synchronous

The existing CRUD application uses a synchronous SQLAlchemy `Session` and synchronous database operations:

```text
def router -> def service -> def repository -> Session -> PostgreSQL
```

FastAPI safely runs the outer normal route in its threadpool. Changing only the router to `async def` would leave the database operations blocking and would move them onto the event-loop path.

A fully async database design requires `AsyncSession`, an async SQLAlchemy engine, an asyncio-compatible PostgreSQL driver, and awaited repository/service/router calls together. That larger refactor is intentionally outside this module.

## Database connection pool remains a limit

Async I/O and a larger synchronous threadpool can improve how many requests the application can wait on concurrently, but database work is still bounded by the database connection pool. If all database connections are in use, additional requests wait until a connection becomes available.

- **Threadpool size** limits concurrent synchronous application work.
- **Event loop** coordinates many awaitable operations without holding one thread per request.
- **Database connection pool** limits concurrent database connections and database operations.

Increasing the threadpool beyond the database pool does not create more concurrent database queries; it can only create more requests waiting for a connection.

## I/O-bound versus CPU-bound work

| Work type | Async helps? | Example |
|---|---|---|
| I/O-bound | Yes, when the library provides an awaitable operation. | Waiting for an external HTTP API. |
| CPU-bound | No. Async does not make calculations faster. | Large in-process image processing. |

Neither the synchronous threadpool nor the async event loop is intended for CPU-heavy work. The threadpool isolates blocking synchronous I/O, while the event loop coordinates non-blocking, awaitable I/O. For CPU-heavy work, use separate processes or a background-worker system.
