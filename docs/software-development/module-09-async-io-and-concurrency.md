# Module 09 — Async I/O and Concurrency Limits

Concurrency design should match the work a component performs and the behavior
of the libraries it calls. The goal is not to make every component
asynchronous, but to choose a model that allows useful work to make progress
while other operations wait.

## Match concurrency choices to the work

Choose concurrency tools that fit the operations and libraries a component
uses. I/O waits can often overlap when the libraries support it; blocking calls
and CPU-heavy work need different handling. Adding asynchronous syntax alone
does not make blocking work concurrent or make an external operation faster.

| Workload | Synchronous approach | Asynchronous approach | Guidance |
|---|---|---|---|
| I/O-bound work with blocking libraries | The operation blocks its worker while waiting. Other requests can progress if the framework provides additional workers. | Async syntax does not help if the library still blocks. | Use the blocking library with an appropriate worker model, or choose an async-compatible library. |
| I/O-bound work with async-compatible libraries | A worker remains occupied while the operation waits. | The task yields while waiting, allowing other ready tasks to progress. | Async can improve concurrency when many operations spend time waiting on I/O. |
| CPU-bound work | Computation occupies the executing worker. | Computation still occupies the event loop unless explicitly offloaded. | Async alone does not speed up CPU work; use suitable parallel processing or a separate worker when needed. |

## Understand where requests wait

Requests pass through components with finite capacity. A limit in one component
can cause a queue there or increase waiting at a downstream dependency. Raising
that limit may simply move the queue to another resource.

```mermaid
flowchart LR
    R[Incoming requests] --> W[Execution capacity]
    W --> A[Application work]
    A --> P[Connection pool]
    P --> D[Database or external service]
    A --> C[CPU capacity]
```

Measure request latency, queueing, worker use, connection-pool use, downstream
response times, and CPU to locate the limiting resource before tuning capacity.

## Keep the full call chain compatible

The request handler, application services, persistence layer, and external
clients all contribute to how a request runs. Changing one layer's execution
style does not make blocking dependencies nonblocking. When adopting
asynchronous I/O, ensure the libraries and calls throughout the relevant path
support it.

For the Python and FastAPI demonstration, including threadpool configuration,
SQLAlchemy's synchronous persistence path, and k6 observations, see
[Async I/O](../async-io.md).

