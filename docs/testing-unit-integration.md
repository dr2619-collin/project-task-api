# Unit and Integration Testing

This document explains the automated-test layout introduced in Module 06. It is a living reference: add explanations here as the test suite grows in later modules.

## Starting point: pytest, TestClient, and Testcontainers

**pytest** is Python's general-purpose test framework, similar to JUnit in Java. It discovers test files, runs test functions, provides fixtures, evaluates assertions, and reports passed, failed, skipped, and warning results.

In this project, run the suite with:

```bash
uv run pytest
```

That command means:

```text
uv runs pytest
pytest discovers tests/
pytest runs unit and integration tests
pytest reports the results
```

pytest uses these naming conventions by default:

- Files named `test_*.py` contain tests.
- Functions named `test_*` are test cases.
- A function marked `@pytest.fixture` provides reusable test setup.

`TestClient` is the FastAPI/Starlette testing client used for API integration tests. It sends HTTP-style requests directly to the FastAPI application in the same Python process, without starting Uvicorn or listening on port 8000.

Testcontainers is a separate testing tool that uses Docker Desktop to start the temporary PostgreSQL database needed by integration tests. Pytest coordinates all three tools.

## Running the tests

Start Docker Desktop, then run this command from the repository root:

```bash
uv run pytest
```

Docker Desktop is needed only for tests that use the temporary PostgreSQL database. Unit tests do not start Docker or require a database.

## Test layout

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

The `test_` prefix is a pytest convention. Pytest automatically discovers files named `test_*.py` and functions named `test_*`.

The test directories mirror the corresponding application packages. Pytest is configured with `--import-mode=importlib` in `pyproject.toml`, so files with the same name in different resource directories are imported by their full path.

### `tests/unit/`

Unit tests verify Python behavior in isolation. The current tests cover Pydantic schema rules and the business rules exercised by the in-memory Project and Task services.

The database-service tests mock repository and session collaborators so they can verify service decisions and transaction boundaries without PostgreSQL. The in-memory-service tests use a fresh `InMemoryStore` for each test. None of these unit tests make HTTP requests or start Docker.

### Service coverage in Module 06

The service tests cover representative success scenarios and meaningful rule or missing-resource branches:

| Service | Public methods covered |
|---|---|
| `DatabaseProjectService` | repository delegation, transaction use, and missing-project translation with mocked collaborators |
| `DatabaseTaskService` | parent-project validation, repository delegation, and transaction use with mocked collaborators |
| `InMemoryProjectService` | create, list, get, replace, related-task lookup, and delete rules |
| `InMemoryTaskService` | create, list, get, replace, parent-project validation, and delete |

The tests verify service-owned behavior at two levels: mocks isolate database-service decisions, while the in-memory tests verify rules and generated IDs directly. Repository and API integration tests verify the real PostgreSQL behavior.

### Schema coverage in Module 06

The schema tests cover every public Pydantic schema class:

| Resource | Request schemas | Response schema |
|---|---|---|
| Project | `ProjectInput` | `ProjectResponse` |
| Task | `TaskInput` | `TaskResponse` |

They verify every application-defined schema rule: required fields, inclusive length limits, rejected values just outside those limits, whitespace stripping, unknown-field rejection, defaults, positive identifiers, and response serialization from ORM model attributes. These tests verify the contract rules this project declares; they do not attempt to reproduce Pydantic's own internal test suite.

Within `tests/unit/`, mirror the relevant application layer. For example:

```text
app/services/projects/in_memory.py -> tests/unit/services/projects/test_in_memory.py
app/services/tasks/in_memory.py    -> tests/unit/services/tasks/test_in_memory.py
app/schemas/projects.py -> tests/unit/schemas/test_projects.py
```

As the project grows, pure schema or utility behavior can similarly use folders such as `tests/unit/schemas/` or `tests/unit/utils/`.

### `tests/integration/`

Integration tests send requests through the FastAPI application with `TestClient`. They exercise several layers together:

```text
TestClient -> router -> service -> repository -> SQLAlchemy -> PostgreSQL
```

The PostgreSQL database is a temporary container created by Testcontainers, not the local `project_task` development database.

Integration tests deliberately cross all application layers, so name them for the API resource or user-visible behavior rather than a specific source layer:

```text
POST and GET /projects -> tests/integration/routers/test_projects.py
POST /tasks and GET /projects/{id}/tasks -> tests/integration/routers/test_tasks.py
ProjectRepository -> tests/integration/repositories/test_projects.py
TaskRepository -> tests/integration/repositories/test_tasks.py
```

Router tests are integration tests because they send an HTTP request through FastAPI and use the real service, repository, ORM, and PostgreSQL layers.

### Module 06 API integration tests are contract-aware

Module 06 covers every Project and Task endpoint on a successful path. The tests assert the expected path behavior, successful status code, response body, and persisted outcome. This gives useful confidence in the normal API workflow and checks contract-like details such as `201 Created` after a successful `POST`.

These tests write their expectations directly in Python. For example, a test says that `POST /projects` returns `201` and a Project body containing an ID. It does not yet use the generated OpenAPI document as its source of truth.

## Why each layer uses this test level

The course does not use the rule “every file must have a unit test.” Instead, each behavior is tested at the level that gives meaningful confidence without merely repeating implementation details.

| Layer | Primary test level | Reason |
|---|---|---|
| Pydantic schemas | Unit | Type hints, field constraints, defaults, and model configuration run in Python without HTTP or a database. |
| Services | Unit | In-memory implementations verify rules directly; database-service tests use mocked repositories and sessions to isolate service decisions. |
| Repositories | Integration | A mocked Session can prove that a method called `add()` or `scalars()`, but cannot prove that the SQLAlchemy query works with PostgreSQL. |
| ORM models | Integration | Foreign keys, table mappings, generated IDs, and database constraints must be verified by a real PostgreSQL database. |
| Routers | Integration | An endpoint is meaningful only when FastAPI parses the request, resolves dependencies, calls the layers, and returns HTTP. |
| OpenAPI contract | Conformance, Module 07 | The API must be tested from a consumer's perspective against its published OpenAPI document. |

### Why repositories are not unit-tested with mocks

Repository methods are mostly SQLAlchemy operations. A mock-based test such as “`session.get()` was called with these arguments” repeats the implementation without proving that PostgreSQL returns the correct records.

Repository and ORM tests use the Testcontainers PostgreSQL database. They verify observable persistence behavior together, including Project and Task creation, generated IDs, Task-to-Project relationships, filtering, ordering, existence checks, and the Task foreign-key constraint.

### Why schema and service unit tests are still useful

A Pydantic schema can be tested directly because validation is its behavior. Schema unit tests should cover the constraints and configuration this application defines, including required fields, length limits, whitespace stripping, defaults, positive identifiers, and rejection of undocumented fields.

A service can be tested directly because it owns decisions such as “a Task's Project must exist” and “a Project with Tasks cannot be deleted.” Database-service tests use mocked repositories and session factories to verify those decisions and the transaction boundary without starting PostgreSQL. The in-memory-service tests exercise the same kinds of rules with a real `InMemoryStore`.

## Module 07: API conformance and negative testing

Module 07 does not repeat all unit tests through HTTP. It adds consumer-facing tests in `tests/conformance/`.

```text
tests/conformance/
├── test_openapi_contract.py
└── test_negative_requests.py
```

These tests use `TestClient` and the same temporary PostgreSQL Testcontainer. They verify the public API boundary:

- The generated `/openapi.json` document is present and structurally valid.
- Declared paths, operations, request schemas, response schemas, and status codes match the intended API contract.
- Representative invalid requests receive predictable HTTP responses: `422` for invalid request data, `404` for missing resources, and `409` for the Project-with-Tasks conflict.
- Schema-driven testing with Schemathesis can generate additional valid, invalid, and boundary requests from the OpenAPI document.

Negative tests intentionally send invalid or disallowed input. They pass when the API rejects that input with the expected status and response shape. They complement schema unit tests by proving what a real client receives over HTTP.

Module 07 overlaps deliberately with Module 06, but has a different question:

| Module 06 integration tests | Module 07 conformance tests |
|---|---|
| Does a valid API workflow work? | Does the implementation honor the published API contract? |
| Tests every Project and Task endpoint on a successful path | Tests OpenAPI structure plus representative success, invalid, missing, boundary, and conflict behavior |
| Expected status and body are written directly in the test | Expected public behavior is checked against the OpenAPI document and approved contract expectations |
| Verifies persistence through the normal application flow | Verifies what API consumers can safely depend on |

Module 07 tests are also full API tests with `TestClient` and PostgreSQL; they are not router-only tests.

### `tests/conformance/` on Module 07

The Module 07 branch adds a `conformance/` directory. Those tests reuse the same Testcontainers fixtures while checking whether the running API follows its generated OpenAPI contract and handles invalid requests predictably.

## Why `conftest.py` is in `tests/`

`conftest.py` is a special pytest file name. Pytest discovers it automatically; test files do not import it.

The directory that contains a `conftest.py` determines which tests can use its fixtures:

```text
tests/conftest.py              -> unit, integration, and conformance tests
tests/integration/conftest.py  -> integration tests only
```

The current fixtures are in `tests/conftest.py` because both Module 06 integration tests and future Module 07 conformance tests need the temporary PostgreSQL database and `TestClient`.

Although the fixtures are available to every test below `tests/`, pytest runs a fixture only when a test requests it. The unit tests do not request the database fixtures, so they do not start Docker.

## Fixtures and fixture scope

A pytest fixture is reusable test setup. A fixture can provide a simple Python object, prepare database records, start an external dependency, or clean up after a test.

For example, a fixture can provide predictable in-memory test data:

```python
@pytest.fixture
def project() -> Project:
    return Project(
        id=1,
        name="Course API",
        description="Course demonstration",
    )
```

A test requests that setup by naming the fixture as a parameter:

```python
def test_get_project_returns_existing_project(project: Project) -> None:
    ...
```

Fixtures can also depend on other fixtures. Pytest resolves and runs those dependencies automatically.

### Fixture scopes

| Scope | Lifetime | Use in this project |
|---|---|---|
| Default (`function`) | Once for each test function that requests it | Fresh test data, a clean database, a database Session, and a TestClient. |
| `session` | Once for one complete pytest command | The temporary PostgreSQL Testcontainer and its configured SQLAlchemy engine. |

The boundary for `scope="session"` is the pytest command, not a test file.

```bash
uv run pytest
```

This starts one pytest session. When an integration or conformance test first requests `postgres_container`, Testcontainers starts one temporary PostgreSQL database. Every integration test in that command shares the same container:

```text
tests/integration/routers/test_projects.py
tests/integration/routers/test_tasks.py
tests/integration/repositories/test_projects.py
tests/integration/repositories/test_tasks.py
```

The container is removed after the command completes. Running another pytest command later creates a new pytest session and therefore a new PostgreSQL container:

```bash
uv run pytest tests/integration/routers/test_projects.py
```

The command above starts one container only for that file's test run. It does not reuse a container from a previous command.

`scope="session"` describes the lifetime of the **pytest test run**. It is different from a SQLAlchemy `Session`, which is the application's database unit-of-work object.

## Shared fixtures

### `postgres_container`

`postgres_container` has **session scope**, so it starts one PostgreSQL 18 container for the complete pytest command, not once per test file:

```text
pytest begins
  -> First integration test requests postgres_container
  -> Testcontainers starts PostgreSQL once
  -> integration and conformance tests use it
pytest ends
  -> Testcontainers removes PostgreSQL
```

The fixture obtains the temporary database connection URL from Testcontainers and sets `DATABASE_URL` before the application creates its database infrastructure. This ensures SQLAlchemy connects to the container instead of the local development database.

The fixture specifies `driver="psycopg"` because this project uses Psycopg 3. Testcontainers otherwise generates a URL for its default Psycopg 2 driver.

### `test_engine`

`test_engine` also has session scope. It imports the ORM models so `Base.metadata` knows about both tables, then calls the same `create_database(Settings())` function used by the application. The returned engine points at the temporary container.

### `reset_database`

`reset_database` has the default **function scope**, meaning pytest runs it once for each integration test that requests it. Although all integration tests share one container, they do not share test data.

Before a test, it drops and recreates the `projects` and `tasks` tables. After the test, it drops the tables again. This gives every integration test an empty, independent database without starting another PostgreSQL container.

### `client`

`client` depends on `reset_database`, so the database is ready before a test receives a `TestClient`.

It uses `TestClient` as a context manager. Entering that context runs FastAPI's lifespan function, similar to an application startup. The API therefore creates any missing tables through `Base.metadata.create_all(...)`, though `reset_database` has already created them for test isolation.

### `db_session`

`db_session` has function scope and provides one real SQLAlchemy `Session` to a repository integration test. It depends on `reset_database`, so it uses the same temporary PostgreSQL container but starts with empty tables. The fixture rolls back any uncommitted transaction after the test before the tables are dropped.

## Fixture dependency flow

```text
integration test
  -> client
      -> reset_database
          -> test_engine
              -> postgres_container
```

This order explains why a test can simply declare `client` as a function parameter. Pytest resolves and runs the dependent fixtures automatically.

## Test names and readability

Use names that describe the expected behavior rather than the implementation detail:

```python
def test_delete_project_rejects_project_with_tasks() -> None:
    ...
```

This makes a failing test report meaningful before someone opens the test file.

## Current test levels

| Test level | Example question | Current example |
|---|---|---|
| Unit | Does a Python-level rule work in isolation? | A Project with Tasks cannot be deleted. |
| Integration | Do persistence and API layers work together with PostgreSQL? | Create a Project, then retrieve it over HTTP. |
| Conformance | Does actual API behavior match the OpenAPI contract? | Added in Module 07. |
