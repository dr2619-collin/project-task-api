# Async I/O

## Compare sync vs. async I/O

Module 09 compares two public routes that simulate waiting for a slow external dependency. The simulated wait is not useful application work; it stands in for time spent waiting for a remote HTTP API, file system, cloud service, or an async-compatible database driver.

| Route | Implementation | What the demo shows |
|---|---|---|
| `GET /async-demo/sync-wait?seconds=0.25` | A normal `def` route with `time.sleep()` | FastAPI places blocking synchronous work in its threadpool. |
| `GET /async-demo/async-wait?seconds=0.25` | An `async def` route with `await asyncio.sleep()` | The coroutine yields to the event loop while it waits. |

Both endpoints are public so the demonstration focuses on concurrency rather than authorization. They accept an optional `seconds` query parameter from `0` through `3`; valid requests return `200 OK`. The simulated `asyncio.sleep()` is a deterministic stand-in for waiting on an external service, file operation, or async-compatible database driver.

## k6 load script

[k6](https://grafana.com/docs/k6/latest/) is a command-line load-testing tool. Unlike pytest, it starts virtual users that make real HTTP requests to a running API and then summarizes timing, request-count, and check results.

The course script is [scripts/load/async-demo.js](../scripts/load/async-demo.js). Read its comments to see how the virtual-user scenario, command-line endpoint selection, HTTP request, and response check work together.

The k6 script starts 80 virtual users, each making one request. With the same simulated `0.25`-second (250 ms) wait, async requests can wait together. Synchronous requests use threadpool workers, so requests beyond the configured worker limit wait for an earlier group to finish.

| Scenario | Thread pool size | Total requests | Each request wait time | Expected request batches | Expected completion time |
|---|---:|---:|---:|---|---|
| Synchronous route | 40 threads (default) | 80 | 250 ms | 2 batches (40 concurrent requests each) | `2 × 250 ms = 500 ms` |
| Synchronous route | 10 threads | 80 | 250 ms | 8 batches (10 concurrent requests each) | `8 × 250 ms = 2,000 ms` |
| Asynchronous route | Not used | 80 | 250 ms | 1 batch (80 concurrent waits) | `1 × 250 ms = 250 ms` |

Each synchronous batch can run up to the thread-pool size of requests
concurrently; batches run one after another. The async route can have all 80
requests waiting concurrently while their coroutines yield at `await`.

The completion times are useful expectations for the total run and high-percentile request durations. Actual k6 measurements include local scheduling, startup, and network overhead, so they will be somewhat higher and can vary by machine.

This is a concurrency demonstration, not a production benchmark. The two endpoints use no database and no external network call, so the comparison isolates how the application waits.

## Run the demo

### What you will compare

Each run sends 80 requests that each simulate a 250 ms wait:

1. A synchronous route with a 40-thread pool.
2. The same synchronous route with a 10-thread pool, which makes queued
   requests visible.
3. An asynchronous route while the pool remains at 10 threads. Its awaitable
   waits do not consume synchronous threadpool capacity.

### 1. Install k6

macOS with Homebrew:

```bash
brew install k6
```

Windows with Windows Package Manager (run in PowerShell or Windows Terminal):

```powershell
winget install k6 --source winget
```

See the [k6 Windows installation instructions](https://grafana.com/docs/k6/latest/set-up/install-k6/#windows)
for other Windows installation options.

For Linux, Docker, and other installation options, see the official
[Install k6](https://grafana.com/docs/k6/latest/set-up/install-k6/)
instructions.

### Run 1: synchronous route with a 40-thread pool

1. Start the API from the repository root in one terminal:

   macOS or Linux:

   ```bash
   SYNC_THREADPOOL_SIZE=40 uv run uvicorn app.main:app --reload
   ```

   Windows PowerShell:

   ```powershell
   $env:SYNC_THREADPOOL_SIZE = "40"; uv run uvicorn app.main:app --reload
   ```

2. In a second terminal at the repository root, execute the k6 script:

   macOS or Linux:

   ```bash
   ENDPOINT=sync-wait k6 run scripts/load/async-demo.js
   ```

   Windows PowerShell:

   ```powershell
   $env:ENDPOINT = "sync-wait"; k6 run scripts/load/async-demo.js
   ```

With 80 requests, this should require two batches of 40 blocking waits.

### Run 2: synchronous route with a smaller pool

1. Stop the API from Run 1 with `Ctrl+C`, then restart it from the repository
   root in one terminal with a 10-thread synchronous threadpool:

   macOS or Linux:

   ```bash
   SYNC_THREADPOOL_SIZE=10 uv run uvicorn app.main:app --reload
   ```

   Windows PowerShell:

   ```powershell
   $env:SYNC_THREADPOOL_SIZE = "10"; uv run uvicorn app.main:app --reload
   ```

2. In a second terminal at the repository root, execute the same synchronous
   k6 test again:

   macOS or Linux:

   ```bash
   ENDPOINT=sync-wait k6 run scripts/load/async-demo.js
   ```

   Windows PowerShell:

   ```powershell
   $env:ENDPOINT = "sync-wait"; k6 run scripts/load/async-demo.js
   ```

This time, the 80 requests should require eight batches of 10 blocking waits.

### Run 3: asynchronous route with the smaller pool

1. Keep the API running with the 10-thread pool from Run 2. Do not restart it.

2. In a second terminal at the repository root, execute the async k6 test:

   macOS or Linux:

   ```bash
   ENDPOINT=async-wait k6 run scripts/load/async-demo.js
   ```

   Windows PowerShell:

   ```powershell
   $env:ENDPOINT = "async-wait"; k6 run scripts/load/async-demo.js
   ```

The route's `await asyncio.sleep()` yields to the event loop, so its 80 waits
can overlap even though the synchronous threadpool remains limited to 10.

k6 reports request duration, percentile, request-count, and failure information at the end of each run. Do not compare a single laptop's numbers to a universal target; compare the two runs made on the same machine.

## k6 results

Record the `http_req_duration` values from each k6 summary in this comparison table. They represent individual client request durations.

| Scenario | Thread pool size | Each request wait time | Expected request batches | Expected completion time | Actual average request duration | Actual p95 request duration |
|---|---:|---:|---|---|---:|---:|
| Synchronous route | 40 threads (default) | 250 ms | 2 batches | `2 × 250 ms = 500 ms` | 530.35 ms | 533.16 ms |
| Synchronous route | 10 threads | 250 ms | 8 batches | `8 × 250 ms = 2,000 ms` | 2,060 ms | 2,060 ms |
| Asynchronous route | Not used | 250 ms | 1 batch (80 concurrent waits) | `1 × 250 ms = 250 ms` | 268.03 ms | 269.60 ms |

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
