# Project and Task Management API

The Project and Task Management API organizes work into Projects and Tasks. Users can create, view, replace, and delete both resources, and each Task belongs to one Project. This repository is the cumulative course demonstration for SDEV 3310; every module branch builds on the previous one.

## Module 05 scope

Module 05 replaces temporary Python lists with PostgreSQL persistence and introduces a layered source-code structure:

- **Routers** handle HTTP requests and responses.
- **Services** contain business rules and coordinate operations.
- **Repositories** perform database operations.
- **ORM models** map Python classes to PostgreSQL tables.
- **Pydantic schemas** validate API request and response data.

The application uses SQLAlchemy 2.x as its ORM and Psycopg as the PostgreSQL driver. Projects and Tasks now remain available after the API restarts.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- PostgreSQL running on your computer

`uv` manages the Python version, virtual environment, and project dependencies. PostgreSQL runs as a separate local service in this module; a later deployment module will run the API and database in containers.

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

Create a database for the application. From the PostgreSQL command-line client:

```sql
CREATE DATABASE project_task_api;
```

Copy the sample configuration file:

```bash
cp .env.example .env
```

Edit `.env` and replace `change-me` with the password for your local PostgreSQL user:

```text
DATABASE_URL=postgresql+psycopg://postgres:change-me@localhost:5432/project_task_api
```

The URL identifies the database dialect and driver, username, password, host, port, and database name. Do not commit `.env`; it is excluded by `.gitignore`.

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

The development server is available at `http://localhost:8000`. On startup, this course version creates the `projects` and `tasks` tables when they do not exist. A later module can introduce versioned database migrations.

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
└── README.md
```

This is a layer-first organization, which makes each responsibility visible while students are learning the architecture. A later course discussion can compare layer-first and feature-first organizations.
