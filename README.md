# Project and Task Management API

The Project and Task Management API organizes work into Projects and Tasks. Users can create, view, replace, and delete both resources, and each Task belongs to one Project. This repository is the cumulative course demonstration for SDEV 3310; every module branch builds on the previous one.

## Module 06 scope

Module 06 adds automated tests to the persistent, layered API from Module 05. The test suite uses pytest, FastAPI's Starlette-based `TestClient`, and Testcontainers to start an isolated PostgreSQL database automatically for integration tests.

The application retains the Module 05 persistence architecture:

- **Routers** handle HTTP requests and responses.
- **Services** contain business rules and coordinate operations.
- **Repositories** perform database operations.
- **ORM models** map Python classes to PostgreSQL tables.
- **Pydantic schemas** validate API request and response data.

The application uses SQLAlchemy 2.x as its ORM and Psycopg as the PostgreSQL driver. Projects and Tasks remain available after the API restarts.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- PostgreSQL running on your computer
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running when you run integration tests

`uv` manages the Python version, virtual environment, and project dependencies. PostgreSQL runs as a separate local service when you run the API. Docker Desktop is used only by Testcontainers during automated integration tests; students do not need to write Docker commands or Dockerfiles.

### Install uv

macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart the terminal and verify the installation:

```bash
uv --version
```

## Set up PostgreSQL

### macOS with Homebrew

1. Install PostgreSQL 18:

```bash
brew install postgresql@18
```

2. Start PostgreSQL manually. Homebrew initializes a local database cluster at `/opt/homebrew/var/postgresql@18`. To run PostgreSQL only when you choose, start and stop that cluster manually:

```bash
# Start PostgreSQL in the background for this development session.
/opt/homebrew/opt/postgresql@18/bin/pg_ctl \
  -D /opt/homebrew/var/postgresql@18 \
  -l /opt/homebrew/var/postgresql@18/server.log start

# Stop PostgreSQL when you are finished.
/opt/homebrew/opt/postgresql@18/bin/pg_ctl \
  -D /opt/homebrew/var/postgresql@18 stop
```

Optional: add short commands to `~/.aliases`:

```bash
alias pgstart='pg_ctl -D /opt/homebrew/var/postgresql@18 start'
alias pgstop='pg_ctl -D /opt/homebrew/var/postgresql@18 stop'
alias pgstatus='pg_ctl -D /opt/homebrew/var/postgresql@18 status'
```

Reload the aliases in the current terminal:

```bash
source ~/.aliases
```

You can then use `pgstart`, `pgstop`, and `pgstatus`. Make sure `~/.aliases` is sourced by your `~/.zshrc` or `~/.bashrc`.

3. Create the course database and its local login role:

```bash
psql -d postgres -f scripts/setup_database.sql
```

`-d postgres` tells `psql` to connect to PostgreSQL's existing administrative database named `postgres`. The setup script runs there because `project_task` does not exist yet.

The script creates the local development role `postgres` with password `postgres`, then creates the `project_task` database owned by that role. Run it only once. If it is run again, PostgreSQL reports that the role and database already exist; it does not replace or delete them.

4. Configure the application. Copy the sample configuration file:

```bash
cp .env.example .env
```

The local course-demo connection uses the role and password created by the script:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/project_task
```

The URL identifies the database dialect and driver, username, password, host, port, and database name. This username and password are for local course development only. Do not commit `.env`; it is excluded by `.gitignore`.

To see SQLAlchemy-generated SQL in the development-server terminal, set this value in `.env`:

```text
DATABASE_ECHO_SQL=true
```

Leave it set to `false` when SQL logging is not needed; generated SQL can be noisy.

### How the application creates tables

The setup script creates the database and login role. The application creates the `projects` and `tasks` tables when it starts for the first time against that empty database.

Each SQLAlchemy ORM model contains the table details. For example, the `Project` model declares its table name and primary key:

```python
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
```

The `Task` model declares its table name and the foreign key that connects each Task to a Project:

```python
class Task(Base):
    __tablename__ = "tasks"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
```

When FastAPI starts, this code collects the table definitions from the ORM models and asks SQLAlchemy to create any missing tables, columns, primary keys, foreign keys, and indexes:

```python
@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
```

`create_all()` runs at every API startup, but it creates only tables that do not already exist. After the first successful startup, it leaves the existing tables unchanged. It does not update an existing table when an ORM model changes.

For this first persistence module, automatic creation keeps the setup focused on models, sessions, and layers. In a production application, use database migrations—commonly Alembic with SQLAlchemy—to version and apply later schema changes deliberately.

For a deeper explanation of sessions, transactions, and database connections, see [Database Sessions and Connection Pooling](docs/database-sessions-and-connection-pooling.md).

## Install dependencies

From the repository root, run:

```bash
uv sync
```

If the required Python version is unavailable, `uv sync` downloads it. It also creates the virtual environment and installs the dependencies recorded in `uv.lock`.

## Run the API

```bash
uv run uvicorn app.main:app --reload --env-file .env
```

- FastAPI defines routes and handles API requests.
- Uvicorn listens for HTTP connections and passes requests to FastAPI.
- `uv` manages the Python environment and runs the installed command.
- `--reload` restarts the development server after source-code changes.
- `--env-file .env` makes the database URL available to the application.

The development server is available at `http://localhost:8000`. On startup, this course version creates the `projects` and `tasks` tables when they do not exist.

After the first successful startup, confirm that the `projects` and `tasks` tables were created in `project_task`.

From a terminal, run:

```bash
psql -h localhost -U postgres -d project_task -W -c '\dt'
```

Enter the local course-demo password, `postgres`, when prompted. The result should list the `projects` and `tasks` tables in the `public` schema.

You can also use [pgAdmin](https://www.pgadmin.org/download/), a PostgreSQL GUI client. Connect with host `localhost`, port `5432`, username `postgres`, password `postgres`, and database `project_task`, then open **Schemas → public → Tables** to inspect the tables.

## Run automated tests

The test suite has two levels:

- **Unit tests** isolate one business rule with mocks; they do not use HTTP or a database.
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

For an explanation of the test folders, shared fixtures, and Testcontainers lifecycle, see [Testing the Project and Task Management API](docs/testing.md).

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

Repositories call `flush()` so SQLAlchemy sends changes to the current transaction. Services call `commit()` when an operation succeeds or `rollback()` when it fails. This keeps transaction decisions with the use case instead of the HTTP or database layer.

![Request flow through the application layers](docs/sequence-diagram.png)

## Project structure

```text
project-task-api/
├── app/
│   ├── database/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
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
│   │   ├── projects.py
│   │   └── tasks.py
│   ├── exceptions.py
│   └── main.py
├── .env.example
├── pyproject.toml
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── repositories/
│   │   ├── test_projects_api.py
│   │   └── test_tasks_api.py
│   └── unit/
│       ├── schemas/
│       └── services/
└── README.md
```

This is a layer-first organization, which makes each responsibility visible while students are learning the architecture. A later course discussion can compare layer-first and feature-first organizations.
