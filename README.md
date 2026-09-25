# Project and Task Management API

The Project and Task Management API organizes work into Projects and Tasks. Users can create, view, replace, and delete both resources, and each Task belongs to one Project. This repository is the cumulative course demonstration for SDEV 3310; every module branch builds on the previous one.

## Module 06 scope

Module 06 adds automated tests to the persistent, layered API from Module 05. The test suite uses pytest, FastAPI's Starlette-based `TestClient`, and Testcontainers to start an isolated PostgreSQL database automatically for integration tests.

For detailed unit and integration test implementation information, see [Unit and Integration Testing](docs/testing-unit-integration.md).

The application retains the Module 05 persistence architecture:

- **Routers** handle HTTP requests and responses.
- **Services** contain business rules and coordinate operations.
- **Repositories** perform database operations.
- **ORM models** map Python classes to PostgreSQL tables.
- **Pydantic schemas** validate API request and response data.

The application uses SQLAlchemy 2.x as its ORM and Psycopg as the PostgreSQL driver. Projects and Tasks remain available after the API restarts.

The service layer has database-backed and in-memory implementations behind the same service contracts. PostgreSQL is the default; set `STORAGE_BACKEND=memory` in `.env` to run the application with process-local lists instead.

See [Software Development Principles and Practices](docs/software-development-principles.md) for the development practices demonstrated by the current module.

## Setup

Follow the setup guide for your operating system:

- [Windows setup](docs/windows-setup.md)
- [macOS setup](docs/macos-setup.md)

The setup guide includes the project clone step. If you already cloned the
repository, skip that step and continue with the remaining setup.

## Clone the project (skip if already done)

If you did not clone the repository from the setup guide, run these commands in
your terminal:

```text
git clone https://github.com/dr2619-collin/project-task-api.git
cd project-task-api
git switch module-06
```

## Install dependencies

From the repository root, run:

```bash
uv sync
```

If the required Python version is unavailable, `uv sync` downloads it. It also creates the virtual environment and installs the dependencies recorded in `uv.lock`.

## Run the API

Before starting the API, copy the sample environment file:

```bash
cp .env.example .env
```

The local connection uses the database user account and password created by the database setup script:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/project_task
```

The URL identifies the database dialect and driver, username, password, host, port, and database name. The `postgres:postgres` username and password are intentionally simple credentials for this local course demo only. Never reuse them in production; load unique credentials at runtime from a secret manager such as HashiCorp Vault or AWS Secrets Manager, or from protected environment configuration. Do not commit `.env`; it is excluded by `.gitignore`.

`DATABASE_URL` is required when `STORAGE_BACKEND=database`. It has no credential
default in the application source. The in-memory backend does not require a
database URL.

Choose the storage backend in `.env` before starting the API:

```text
STORAGE_BACKEND=database
```

Use `database` for PostgreSQL persistence (the default), or set it to `memory` to use process-local in-memory data while experimenting. The in-memory backend protects compound list operations with a process-local lock, but data is still lost when the API stops and is not shared across workers or containers.

To see SQLAlchemy-generated SQL in the development-server terminal, set this value in `.env`:

```text
DATABASE_ECHO_SQL=true
```

Leave it set to `false` when SQL logging is not needed.

```bash
uv run uvicorn app.main:app --reload
```

- FastAPI defines routes and handles API requests.
- Uvicorn listens for HTTP connections and passes requests to FastAPI.
- `uv` manages the Python environment and runs the installed command.
- `--reload` restarts the development server after source-code changes.
- `Settings` reads and validates `.env` and environment variables when the
  application starts.

The development server is available at `http://localhost:8000`. On startup, the application creates the `projects` and `tasks` tables when they do not exist.

After the first successful startup, confirm that the `projects` and `tasks` tables were created in `project_task`.

From a terminal, run:

```bash
psql -h localhost -U postgres -d project_task -W -c '\dt'
```

On Windows PowerShell, if PostgreSQL has not yet been added to `PATH`, run:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d project_task -W -c "\dt"
```

Enter the local password, `postgres`, when prompted. The result should list the `projects` and `tasks` tables in the `public` schema.

You can also use **pgAdmin 4**, a PostgreSQL GUI client (already installed by the Windows installer; macOS users may install it separately).

In pgAdmin 4:

- Host: `localhost`
- Port: `5432`
- Username: `postgres`
- Password: `postgres`
- Database: `project_task`

Then open **Schemas → public → Tables** to inspect the tables.

For a deeper explanation of sessions, transactions, and database connections, see [Database Sessions and Connection Pooling](docs/database-sessions-and-connection-pooling.md).

## Run automated tests

If Docker Desktop is not installed and running, follow the Docker Desktop setup instructions for your operating system: [Windows](docs/windows-setup.md#6-install-docker-desktop-for-module-06-testing) or [macOS](docs/macos-setup.md#6-install-docker-desktop-for-module-06-testing).

The test suite has two levels:

- **Unit tests** isolate business rules; some use mocked database collaborators, and others use the in-memory services. They do not use HTTP or PostgreSQL.
- **Integration tests** use `TestClient` to send requests through the API and use a temporary PostgreSQL database.

Before running integration tests, start Docker Desktop. Testcontainers uses Docker Desktop to start a disposable PostgreSQL container automatically. The container is created for the pytest session and removed when the test run finishes. It is never the local `project_task` development database.

Run all tests from the repository root:

```bash
uv run pytest
```

The first run may take longer while Docker downloads the PostgreSQL image. Test data is reset before each integration test, so one test does not affect another.

```text
pytest
  -> Testcontainers starts temporary PostgreSQL
  -> TestClient sends API requests
  -> pytest checks the responses
  -> Testcontainers removes PostgreSQL
```

Run only unit tests:

```bash
uv run pytest tests/unit
```

Run only API router integration tests:

```bash
uv run pytest tests/integration/routers
```

Run one repository integration test file:

```bash
uv run pytest tests/integration/repositories/test_projects.py
```

Choose the smallest test level that gives meaningful confidence. Use
integration tests when correctness depends on framework, ORM, or database
behavior.

For detailed unit and integration test implementation information, see [Unit and Integration Testing](docs/testing-unit-integration.md).

## Explore the API

- `http://localhost:8000/docs` — Swagger UI for exploring and calling endpoints
- `http://localhost:8000/redoc` — ReDoc for reading reference documentation
- `http://localhost:8000/openapi.json` — the machine-readable OpenAPI document

| Method | URL | Operation | Successful status |
|---|---|---|---|
| `GET` | `/projects` | List Projects | `200 OK` |
| `GET` | `/projects/{project_id}` | Get one Project | `200 OK` |
| `POST` | `/projects` | Create a Project | `201 Created` |
| `PUT` | `/projects/{project_id}` | Replace a Project | `200 OK` |
| `DELETE` | `/projects/{project_id}` | Delete a Project | `204 No Content` |
| `GET` | `/projects/{project_id}/tasks` | List one Project's Tasks | `200 OK` |
| `GET` | `/tasks` | List Tasks | `200 OK` |
| `GET` | `/tasks/{task_id}` | Get one Task | `200 OK` |
| `POST` | `/tasks` | Create a Task | `201 Created` |
| `PUT` | `/tasks/{task_id}` | Replace a Task | `200 OK` |
| `DELETE` | `/tasks/{task_id}` | Delete a Task | `204 No Content` |

Create a Project before creating its Tasks:

```json
{
  "name": "Demo Project",
  "description": "Practice layered database persistence"
}
```

Then use the returned Project ID in a Task request:

```json
{
  "title": "Add persistence",
  "description": "Store projects and tasks in PostgreSQL",
  "completed": false,
  "project_id": 1
}
```

The service layer verifies cross-resource rules. A Task cannot reference a nonexistent Project, and a Project cannot be deleted while it still has Tasks. These cases return `404 Not Found` and `409 Conflict`, respectively.

## Request flow

```text
HTTP request
    ↓
Router         HTTP details and Pydantic schemas
    ↓
Service        business rules and transaction decisions
    ↓
Repository     SQLAlchemy queries and persistence operations
    ↓
PostgreSQL     durable Projects and Tasks
```

Repositories call `flush()` so SQLAlchemy sends changes to the current transaction. Each database service operation creates a Session with the application-wide session factory. Read operations use the Session as a context manager, while write operations use `with self._session_factory.begin() as session:` in the service layer. That context manager commits on success and rolls back on an error, keeping transaction decisions with the use case instead of the HTTP or database layer.

```mermaid
classDiagram
    class ProjectService {
        <<abstract>>
        +list_projects()
        +get_project(project_id)
        +create_project(data)
        +replace_project(project_id, data)
        +delete_project(project_id)
        +list_project_tasks(project_id)
    }
    class DatabaseProjectService
    class InMemoryProjectService
    class ProjectRepository
    class TaskRepository
    ProjectService <|-- DatabaseProjectService
    ProjectService <|-- InMemoryProjectService
    DatabaseProjectService --> ProjectRepository : uses

    class TaskService {
        <<abstract>>
        +list_tasks()
        +get_task(task_id)
        +create_task(data)
        +replace_task(task_id, data)
        +delete_task(task_id)
    }
    class DatabaseTaskService
    class InMemoryTaskService
    TaskService <|-- DatabaseTaskService
    TaskService <|-- InMemoryTaskService
    DatabaseTaskService --> TaskRepository : uses

    class ProjectsRouter
    class TasksRouter
    ProjectsRouter *-- ProjectService : injected dependency
    TasksRouter *-- TaskService : injected dependency
```

The routers are composed with the service contracts through dependency injection. They do not construct a database or in-memory service directly. Application startup selects the concrete implementation, while each router continues to call the same parent contract.

![Request flow through the application layers](docs/sequence-diagram.png)

## Project structure

```text
project-task-api/
├── app/
│   ├── database/
│   │   └── session.py
│   ├── config.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── base.py
│   │   ├── project.py
│   │   └── task.py
│   ├── repositories/
│   │   ├── projects.py
│   │   └── tasks.py
│   ├── routers/
│   │   ├── projects.py
│   │   └── tasks.py
│   ├── schemas/
│   │   ├── projects.py
│   │   └── tasks.py
│   ├── services/
│   │   ├── in_memory_store.py
│   │   ├── projects/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── database.py
│   │   │   └── in_memory.py
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── database.py
│   │       └── in_memory.py
│   ├── exceptions.py
│   └── main.py
├── .env.example
├── pyproject.toml
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── repositories/
│   │   └── routers/
│   │       ├── test_projects.py
│   │       └── test_tasks.py
│   └── unit/
│       ├── schemas/
│       └── services/
│           ├── projects/
│           └── tasks/
└── README.md
```

This is a layer-first organization, which makes each responsibility visible while students are learning the architecture.

The same application could use a **feature-first organization**, grouping each resource's router, service, repository, schema, and model together:

```text
project-task-api/
├── app/
│   ├── database/
│   │   └── session.py
│   ├── models/
│   │   └── base.py
│   ├── projects/
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── base.py
│   │       ├── database.py
│   │       └── in_memory.py
│   ├── tasks/
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── base.py
│   │       ├── database.py
│   │       └── in_memory.py
│   ├── dependencies.py
│   └── main.py
├── .env.example
├── pyproject.toml
└── README.md
```
