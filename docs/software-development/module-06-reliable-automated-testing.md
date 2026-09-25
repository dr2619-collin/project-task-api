# Module 06 — Reliable Automated Testing

Module 06 adds automated tests around the persistent layered API from Module 05. The application code remains unchanged; the new code verifies its behavior at several boundaries:

- Unit tests run quickly without HTTP, PostgreSQL, or Docker.
- Repository and API router tests use a real temporary PostgreSQL database.
- Shared pytest fixtures make setup, cleanup, and test lifetimes explicit.

The goal is not to test every line. The goal is to test important behavior at
the level that provides useful confidence.

## Use a balanced testing strategy

Different tests answer different questions:

| Test level | Main question | Current project example |
|---|---|---|
| Unit | Does one Python-level rule work in isolation? | A Project with Tasks cannot be deleted. |
| Integration | Do the application layers work together with PostgreSQL? | Create a Project through HTTP and retrieve it. |
| Conformance | Does the API match its published OpenAPI contract? | Introduced on Module 07. |

The test layout reflects those boundaries:

```text
tests/
├── conftest.py
├── integration/
│   ├── repositories/
│   │   ├── test_projects.py
│   │   └── test_tasks.py
│   └── routers/
│       ├── test_projects.py
│       └── test_tasks.py
└── unit/
    ├── schemas/
    │   ├── test_projects.py
    │   └── test_tasks.py
    └── services/
        ├── projects/
        │   ├── test_database.py
        │   └── test_in_memory.py
        └── tasks/
            ├── test_database.py
            └── test_in_memory.py
```

The test directories mirror the production packages where practical. A test
file named `test_in_memory.py` corresponds to the production module
`in_memory.py`; API router tests are grouped below `integration/routers/`.

## Keep unit tests isolated and purposeful

Unit tests should run without external services. They are useful for rules that
can be checked with small, focused inputs:

- Pydantic field constraints, defaults, and response serialization.
- Missing-resource and parent-child validation decisions.
- In-memory ID generation and deletion rules.

The in-memory service tests use a fresh `InMemoryStore` for each test. They do
not use the local development database and do not start Docker.

## Use mocks as test doubles for database-service decisions

A **test double** is a substitute used to isolate the behavior under test.
Mocks are useful when the question is whether a service makes the correct
decision, not whether SQLAlchemy can execute a query.

The database-service tests replace repository and session-factory collaborators
with mocks. This lets a test verify that:

- `DatabaseProjectService` starts a transaction for a create operation.
- The service delegates creation to `ProjectRepository`.
- A missing Project becomes `ProjectNotFoundError`.
- `DatabaseTaskService` checks the parent Project before creating a Task.
- A missing parent prevents `TaskRepository.create()` from being called.

For example, a database-service test patches the repository at the location
where the service uses it:

```python
with patch(
    "app.services.projects.database.ProjectRepository",
    return_value=repository,
):
    result = DatabaseProjectService(factory).create_project(data)
```

The test does not claim that the SQL query works. That is the repository
integration test's responsibility. It verifies the service's policy and
collaboration with its direct dependency.

## Test repositories with realistic infrastructure

Repositories contain SQLAlchemy queries, so a mock `Session` cannot prove that
the query returns the correct rows, applies ordering, respects foreign keys, or
generates IDs correctly. Repository tests therefore use Testcontainers to run
the actual PostgreSQL database engine.

The repository integration tests verify:

- Project and Task creation and generated IDs.
- Retrieval and ordering.
- Task filtering by Project.
- Project-to-Task relationship checks.
- Replacements and deletes.
- PostgreSQL enforcement of the Task foreign-key constraint.

These tests use the same ORM models, repositories, and SQLAlchemy driver as the
application. The database is temporary and is never the local `project_task`
development database.

## Run integration tests in build pipelines

Testcontainers makes the integration tests practical in a build pipeline. The
same command runs locally and in a CI job:

```bash
uv run pytest
```

When an integration or conformance test requests the PostgreSQL fixture,
Testcontainers asks the available Docker runtime to start the specified
PostgreSQL image. The test suite receives its connection URL, creates its
tables, runs the tests, and removes the container when pytest finishes.

This avoids depending on a manually configured shared test database:

- A developer does not need to create `project_task_test` on their computer.
- A CI job does not need long-lived database credentials or pre-created tables.
- Each test run starts from a known PostgreSQL version and clean database
  state.
- A failed or parallel build is less likely to affect another build's data.

The pipeline runner must provide Docker access, just as a developer must start
Docker Desktop locally. CI platforms often provide this through a Docker-capable
runner or service-container support. If Docker is unavailable, schema and
in-memory unit tests can still run, but the PostgreSQL integration tests should
run in a build environment that supports containers.

## Test API routers through the application boundary

The router tests are integration tests, not isolated router unit tests. They
use Starlette's `TestClient` to send HTTP-style requests directly to FastAPI:

```text
TestClient
    ↓
FastAPI router
    ↓
service
    ↓
repository
    ↓
SQLAlchemy
    ↓
temporary PostgreSQL
```

They cover the successful workflow for the Project and Task endpoints,
including status codes, response bodies, persistence, replacement, deletion,
and the nested Project-to-Task operation. They do not start Uvicorn or listen
on port 8000.

Module 07 adds a separate `tests/conformance/` package. Those tests also use
`TestClient`, but their purpose is different: they verify the generated
OpenAPI document and client-visible negative behavior such as `422`, `404`, and
`409` responses.

## Share fixtures, but isolate each test

`tests/conftest.py` is a special pytest file. Pytest discovers its fixtures
automatically, and tests do not import it directly. It remains at the `tests/`
level because both integration tests and Module 07 conformance tests use the
same fixtures.

The fixture dependency flow is:

```text
API router or repository test
    ↓
client or db_session
    ↓
reset_database
    ↓
test_engine
    ↓
postgres_container
```

The lifetimes are deliberately different:

- `postgres_container` uses `scope="session"`: one temporary PostgreSQL
  container is shared for one `uv run pytest` command.
- `test_engine` also uses session scope: one SQLAlchemy Engine and connection
  pool are configured for that container.
- `reset_database` uses the default function scope: tables are dropped and
  recreated for each test that needs database access.
- `db_session` uses function scope: each repository test receives a fresh
  SQLAlchemy Session.
- `client` uses function scope: each API router test receives a fresh
  `TestClient` and isolated database state. The application creates its own
  SQLAlchemy Session for each service operation.

One pytest command therefore looks like this:

```text
one pytest run
└── one PostgreSQL container and Engine
    ├── repository test 1 → fresh database state and Session
    ├── repository test 2 → fresh database state and Session
    └── API router test   → fresh database state and TestClient
```

The pytest fixture scope is not the same thing as a SQLAlchemy `Session`. A
pytest fixture controls test setup lifetime; a SQLAlchemy Session represents a
database unit of work.

## Make tests deterministic and repeatable

A reliable test should produce the same result when run alone, in a different
order, or on another machine with the documented dependencies. This project
supports that goal by:

- Resetting the database before and after each database test.
- Creating a fresh in-memory store for each in-memory service test.
- Avoiding dependence on the local development database.
- Using predictable request data and explicit assertions.
- Letting pytest control fixture setup and cleanup.
- Running the same PostgreSQL version in Testcontainers for every test run.

The first integration-test run may take longer because Docker may need to
download the PostgreSQL image. Later tests reuse the container during that
pytest command, while each test still receives isolated table state.
