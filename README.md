# Project and Task Management API

This repository contains the course demonstration project for SDEV 3310. The API will grow throughout the semester as new FastAPI and software-development concepts are introduced.

## Module 01 scope

The Module 01 version demonstrates:

- Creating a FastAPI application
- Defining `GET` endpoints
- Returning JSON responses
- Running the application with Uvicorn
- Using FastAPI's generated Swagger UI and OpenAPI document

The application does not manage Projects or Tasks yet. CRUD operations begin in Module 02.

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

If the required Python version is not already available, `uv sync` downloads it automatically. It also creates the project's virtual environment and installs the dependencies recorded in `uv.lock`.

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

- FastAPI defines routes and handles API requests.
- Uvicorn listens for HTTP connections and passes requests to FastAPI.
- `uv` manages the Python environment and runs the installed command.
- `--reload` restarts the development server after source-code changes.

The development server will be available at:

```text
http://localhost:8000
```

## Explore the API

| URL | Purpose |
|---|---|
| `http://localhost:8000/` | API welcome message |
| `http://localhost:8000/health` | Health response |
| `http://localhost:8000/docs` | Interactive Swagger UI |
| `http://localhost:8000/openapi.json` | Machine-readable OpenAPI document |

Example health response:

```json
{
  "status": "healthy"
}
```

## Current project structure

```text
project-task-api/
├── app/
│   ├── __init__.py
│   └── main.py
├── pyproject.toml
└── README.md
```

## Next step

Module 02 introduces Projects as REST resources and implements CRUD operations.
