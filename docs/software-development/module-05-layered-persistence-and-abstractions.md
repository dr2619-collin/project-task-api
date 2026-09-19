# Module 05 — Layered Persistence and Abstractions

Module 05 adds PostgreSQL persistence alongside the temporary in-memory collections.
The application separates:

- HTTP handling
- Business operations
- Database access
- ORM mapping
- API data contracts

Each concern can change without forcing unrelated code to change with it.

## Separate responsibilities into layers

Layered architecture organizes code by the responsibility it owns. In this project, the request path is:

```mermaid
flowchart TD
    A[HTTP request] --> B[Router + Pydantic schemas]
    B --> C[Service]
    C --> D[Repository]
    D --> E[ORM model]
    E --> F[(PostgreSQL)]
```

Layer responsibilities:

- Routers translate HTTP requests into service calls.
- Pydantic schemas validate input and shape API responses.
- Services apply use-case rules, such as preventing deletion of a Project with Tasks.
- Repositories perform database queries and writes.
- ORM models describe tables and relationships.
- PostgreSQL stores durable data and enforces database constraints.

This structure demonstrates the **Single Responsibility Principle (SRP)**:

- HTTP response changes belong in routers.
- Business-rule changes belong in services.
- Query changes belong in repositories.
- Table-mapping changes belong in ORM models.

SRP does not require every class to have one method. It requires the methods in
a class to serve one cohesive responsibility.

The project evidence is visible in these folders:

- [`app/routers/`](../../app/routers/) for HTTP behavior.
- [`app/services/`](../../app/services/) for use cases and transaction ownership.
- [`app/repositories/`](../../app/repositories/) for database queries and writes.
- [`app/models/`](../../app/models/) for SQLAlchemy table mappings.
- [`app/schemas/`](../../app/schemas/) for API data contracts.
- [`app/database/`](../../app/database/) for the Engine, session factory, and
  `DatabaseInfrastructure` that groups them.

## Dependency injection

**Dependency injection (DI)** means that code receives a collaborator it needs instead of locating or constructing that collaborator at every use site. In this module, application startup selects one implementation of each service contract and stores it on `app.state`:

```python
settings = Settings()
database = create_database(settings)
application.state.project_service = DatabaseProjectService(
    database.session_factory
)
application.state.task_service = DatabaseTaskService(
    database.session_factory
)
```

`DatabaseInfrastructure` keeps the application-scoped Engine and session
factory together. Services receive only the session factory because they need
Sessions for operations, not direct control of the Engine or its pool.

The service contracts use Python's `ABC` and `@abstractmethod` features. The database and in-memory implementations inherit from those contracts:

```text
ProjectService
├── DatabaseProjectService
└── InMemoryProjectService

TaskService
├── DatabaseTaskService
└── InMemoryTaskService
```

Set `STORAGE_BACKEND=memory` to select the in-memory pair; the default `database` setting selects PostgreSQL persistence. The routers and their dependencies do not change when the implementation changes.

The dependency functions in [`app/dependencies.py`](../../app/dependencies.py) expose those services to FastAPI routes. A route receives a service through `Depends(...)` rather than constructing it directly:

```python
def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    return service.get_project(project_id)
```

The provider reads the startup-selected service from `request.app.state`:

```python
def get_project_service(request: Request) -> ProjectService:
    return request.app.state.project_service
```

Spring Boot commonly uses container-managed beans and constructor injection;
FastAPI uses dependency functions and `Depends(...)`. The mechanism differs,
but both approaches inject collaborators instead of constructing them inside
request handlers.

## Stateless services and state ownership

Keep REST service instances stateless whenever possible:

- A stateless service does not retain shared application data in its own
  process between requests.
- Shared or durable state belongs in PostgreSQL or another purpose-built store.
- Database services remain stateless while PostgreSQL owns the durable data.
- The in-memory implementation is intentionally stateful for teaching; its
  lists belong to one process and disappear when that process stops.
- Use stateful components only when their behavior requires them, such as
  WebSocket connection managers, workflow coordinators, or caches.

Service lifetime:

- Services are application-scoped because they are stateless.
- They keep the session factory, not one shared database Session.
- A SQLAlchemy Session represents one unit of work.
- Each operation creates and closes its own Session through the factory.
- A Session must not be shared across concurrent requests.

## Polymorphism and the Dependency Inversion Principle

The **Dependency Inversion Principle (DIP)** is a design principle, not a
FastAPI mechanism:

- High-level code should depend on abstractions.
- Concrete implementations should satisfy those abstractions.
- The router depends on `ProjectService` and `TaskService`, not on PostgreSQL or Python lists.

Dependency injection supplies the selected implementation at runtime. The
shared service contract and its database and in-memory implementations also
demonstrate polymorphism.

This is also a concrete example of polymorphism:

- Routers call the same service methods regardless of storage backend.
- The parent service contract defines the operations callers can rely on.
- Child implementations provide database-backed or in-memory behavior.
- Startup can change storage without changing routers or dependencies.
- The in-memory service owns lists and uses a process-local lock for compound operations.
  - The lock protects threads inside one process, not multiple workers or containers.
- The database service owns sessions and delegates persistence to repositories.
- Separate implementation files keep each class focused and independently changeable.

```mermaid
classDiagram
    class ProjectService
    class DatabaseProjectService
    class InMemoryProjectService
    class ProjectRepository
    ProjectService <|.. DatabaseProjectService
    ProjectService <|.. InMemoryProjectService
    DatabaseProjectService --> ProjectRepository : uses
```

The database service creates a repository with the operation-scoped Session:

```python
with self._session_factory.begin() as session:
    repository = ProjectRepository(session)
    project = repository.get_by_id(project_id)
```

Repositories encapsulate SQLAlchemy queries and return ORM objects or `None`.
They do not choose HTTP status codes or application policies. The service
decides what the repository result means for the use case.

## Object-relational mapping

ORM means **object-relational mapping**. SQLAlchemy connects Python classes and
objects to relational tables and rows. In this project, [`app/models/`](../../app/models/)
contains the ORM models and [`app/models/base.py`](../../app/models/base.py)
contains the shared `Base` registry and metadata.

The ORM maps classes to tables, attributes to columns, and relationships to
foreign keys. It converts queries and object changes into SQL and lets the
application work with typed Python objects. PostgreSQL still enforces
constraints, generates integer IDs, runs transactions, and stores the data.

Pydantic schemas solve a different problem: they validate API input, describe
the OpenAPI contract, and serialize API output. Similar fields do not make a
schema and an ORM model interchangeable.

## Communicate through direct collaborators

The **Law of Demeter**, also called the principle of least knowledge, encourages code to communicate with its direct collaborators instead of reaching through several objects to manipulate internal details.

For example:

- A Project route receives a `ProjectService`.
- It calls `service.get_project(project_id)`.
- It does not reach through the service to use a repository or Session.
- The service chooses the repository query without exposing it to the router.

That boundary reduces coupling. The service can change its query, validation,
or transaction handling without changing the router. Layering assigns
responsibilities; the Law of Demeter limits knowledge of collaborator internals.

## Keep application outcomes separate from HTTP responses

Services raise application exceptions such as `ProjectNotFoundError` and
`ProjectHasTasksError` from [`app/exceptions.py`](../../app/exceptions.py).
These exceptions:

- Describe an application outcome.
- Do not import FastAPI or choose an HTTP status code.
- Keep services independent of HTTP.
- Let the same service run from a route, scheduled job, command-line program, or message-bus consumer.

HTTP is a router concern. The helpers in [`app/routers/http_errors.py`](../../app/routers/http_errors.py) translate those application outcomes into FastAPI `HTTPException` objects such as `404 Not Found` or `409 Conflict`. A router catches the application exception and raises the corresponding HTTP response:

```text
Service raises ProjectNotFoundError
    ↓
Router catches the application outcome
    ↓
Router helper creates HTTPException(404, "Project not found")
    ↓
FastAPI sends the HTTP response
```

Package placement follows responsibility:

- `app/exceptions.py` contains shared application outcomes.
- `app/routers/http_errors.py` contains FastAPI-specific translations.
- Services remain usable by HTTP routes, jobs, or message consumers.

## Keep transaction boundaries with the use case

A transaction should cover one complete business operation:

- It may contain more than one database statement.
- It belongs to the service use case, not to HTTP routing.
- The same operation can be reused by a route, message consumer, scheduled job, or command-line command.

In this project, write-oriented methods in the database service use the session factory's `begin()` context manager:

```python
def create_project(self, data: ProjectInput) -> Project:
    with self._session_factory.begin() as session:
        project = ProjectRepository(session).create(data)
        session.refresh(project)
        return project
```

`begin()` creates the Session and transaction. A normal exit from the block commits the transaction; an exception rolls it back and is re-raised. The repository calls `flush()` when it needs PostgreSQL to assign a generated value, such as an ID, before the transaction is committed. `flush()` sends pending work to the database but does not make it permanent.

PostgreSQL uses `READ COMMITTED` by default. Each statement sees committed
data available when that statement starts, and never sees another transaction's
uncommitted changes. A later statement in the same transaction can see a newer
committed value. Concurrent writes to the same row wait for one another, then
the later write can replace the earlier value. This **last update wins** behavior
is acceptable for some fields, but applications needing conflict detection
should use a version column or a conditional update.

For example, if Alice and Bob edit the same Project name, Alice's update can
commit first and Bob's update can wait and then replace it. An optimistic
version check makes the update conditional:

```sql
UPDATE projects
SET name = :new_name, version = version + 1
WHERE id = :project_id AND version = :expected_version;
```

If no row is updated, the service reports a conflict. A transaction can also
use `SELECT ... FOR UPDATE` to lock the row, reread the current value, and
decide whether the later edit is still valid. `FOR UPDATE` holds the row lock
until the transaction commits or rolls back.

Optimistic checks avoid blocking and work well when conflicts are uncommon, but
the caller must handle a rejected update. Pessimistic locks serialize competing
edits, but they keep database locks open and can make other work wait.

Read-only service methods use a Session context manager without a write transaction boundary. In both cases, the Session closes after the operation, returning any borrowed database connection to the Engine's connection pool.

See [Database Sessions and Connection Pooling](../database-sessions-and-connection-pooling.md) for the SQLAlchemy lifecycle and connection-pooling details.
## Configuration controls application behavior

Configuration provides settings that control how the application runs. It can
select implementations, enable or disable features, and adjust limits or
behavior. Follow this flow:

- Load and validate configuration once during application startup.
- Pass typed settings—or specific values—to the infrastructure and services
  that need them.
- Do not reread environment variables inside components.
- Keep business logic independent of where configuration came from.

The `Settings` class in [`app/config.py`](../../app/config.py) is the typed
configuration object. Pydantic Settings reads values from environment
variables and `.env`, converts them to the declared types, applies defaults,
and validates them at startup:

```python
class Settings(BaseSettings):
    database_url: str | None = None
    database_echo_sql: bool = False
    storage_backend: StorageBackend = StorageBackend.DATABASE
```

`StorageBackend` is an enum field inside `Settings`. It defines the supported
persistence choices in one place:

```python
class StorageBackend(StrEnum):
    DATABASE = "database"
    MEMORY = "memory"
```

Using an enum:

- Avoids repeating unvalidated string literals in startup code.
- Makes invalid configuration fail fast with a clear error.
- Prevents silently selecting the wrong implementation.

Environment variables are strings at the process boundary; startup converts
`STORAGE_BACKEND` to the enum before choosing services.

The repository checks in [`.env.example`](../../.env.example) as a safe template that documents the expected settings:

```text
STORAGE_BACKEND=database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/project_task
DATABASE_ECHO_SQL=false
```

Credential safety:

- The `postgres:postgres` value is intentionally simple for this local course demo.
- `DATABASE_URL` is required when the database backend is selected; it has no
  credential default in the application source.
- The in-memory backend can run without a database URL.
- `.env.example` documents a setup; it is not a production credential store.
- Production deployments should load unique credentials at runtime from a secret manager, such as HashiCorp Vault or AWS Secrets Manager, or from protected environment configuration.
- Never reuse the demo password or commit real credentials.

Setup flow:

1. Copy `.env.example` to `.env`.
2. Adjust local database and storage values.
3. Start Uvicorn.
4. `Settings` reads and validates the environment, applies defaults, and selects
   the service implementation.

The real `.env` stays out of Git because it may contain passwords, API keys, or
machine-specific credentials.
