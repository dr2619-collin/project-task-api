# Project and Task Management API

The Project and Task Management API is a simple backend for organizing work into Projects and Tasks. Users can create, view, update, and delete both resources, and each Task belongs to a Project. As the course progresses, the application will gain validation, database persistence, testing, security, and deployment support.

This repository contains the cumulative course demonstration project for SDEV 3310. Each module branch builds on the previous branch as new FastAPI and software-development concepts are introduced.

## Module 02 scope

The Module 02 version demonstrates:

- Treating Projects and Tasks as related REST resources
- Designing collection and item URLs
- Mapping CRUD operations to HTTP methods
- Reading path parameters and JSON request bodies
- Returning appropriate HTTP status codes
- Organizing related routes with `APIRouter`
- Storing demonstration data in memory
- Protecting the relationship between Tasks and Projects

Module 02 intentionally uses dictionaries and a Python list. Pydantic data models and stronger validation arrive in Module 03, while database persistence and repository layers arrive in a later module.

## Requirements

- [uv](https://docs.astral.sh/uv/)

`uv` manages the Python version, virtual environment, and project dependencies.

### Install uv

macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal, then verify the installation:

```bash
uv --version
```

### Set up the project

From the repository root, run:

```bash
uv sync
```

If the required Python version is unavailable, `uv sync` downloads it. It also creates the virtual environment and installs the dependencies recorded in `uv.lock`.

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

- FastAPI defines routes and handles API requests.
- Uvicorn listens for HTTP connections and passes requests to FastAPI.
- `uv` manages the Python environment and runs the installed command.
- `--reload` restarts the development server after source-code changes.

The development server will be available at `http://localhost:8000`.

## Explore the API

Open `http://localhost:8000/docs` to call the endpoints from Swagger UI.

| Method | URL | CRUD operation | Successful status |
|---|---|---|---|
| `GET` | `/` | Read API introduction | `200 OK` |
| `GET` | `/health` | Read API health | `200 OK` |
| `GET` | `/projects` | Read all Projects | `200 OK` |
| `GET` | `/projects/{project_id}` | Read one Project | `200 OK` |
| `POST` | `/projects` | Create a Project | `201 Created` |
| `PUT` | `/projects/{project_id}` | Update a Project | `200 OK` |
| `DELETE` | `/projects/{project_id}` | Delete a Project | `204 No Content` |
| `GET` | `/projects/{project_id}/tasks` | Read one Project's Tasks | `200 OK` |
| `GET` | `/tasks` | Read all Tasks | `200 OK` |
| `GET` | `/tasks/{task_id}` | Read one Task | `200 OK` |
| `POST` | `/tasks` | Create a Task | `201 Created` |
| `PUT` | `/tasks/{task_id}` | Update a Task | `200 OK` |
| `DELETE` | `/tasks/{task_id}` | Delete a Task | `204 No Content` |

Use this JSON body with `POST` and `PUT`:

```json
{
  "name": "Demo Project",
  "description": "Practice REST and CRUD"
}
```

Requesting a Project ID that does not exist returns `404 Not Found`.

Use this JSON body with Task `POST` and `PUT` requests:

```json
{
  "title": "Document the API",
  "description": "Add endpoint examples to the README",
  "completed": false,
  "project_id": 1
}
```

The `project_id` establishes the relationship between a Task and its Project. Creating or updating a Task with a nonexistent Project returns `404 Not Found`. Deleting a Project that still has Tasks returns `409 Conflict`; delete its Tasks first.

## Temporary data

Projects and Tasks are stored in Python lists while the application is running. Changes disappear when the development server restarts. This limitation is intentional: it keeps the focus on REST and CRUD before database persistence is introduced.

## Current project structure

```text
project-task-api/
├── app/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── projects.py
│   │   └── tasks.py
│   ├── __init__.py
│   ├── main.py
│   └── storage.py
├── pyproject.toml
└── README.md
```

The project uses a simple layer-first structure. Route handlers live in `app/routers/`; service and repository layers can be added when the course introduces the responsibilities they contain.

## Next step

Module 03 introduces Pydantic models and request validation.
