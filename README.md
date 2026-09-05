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

See [Software Development Principles and Practices](docs/software-development-principles.md) for the development practices demonstrated by the current module.

## Setup

Follow the setup guide for your operating system:

- [Windows setup](docs/windows-setup.md)
- [macOS setup](docs/macos-setup.md)

## Clone the project

After completing the setup guide, run these commands in your terminal:

```text
git clone https://github.com/dr2619-collin/project-task-api.git
cd project-task-api
git switch module-01
```

## Install project dependencies

From the `project-task-api` folder, run:

```text
uv sync
```

`uv` installs the required Python version when necessary, creates the project's virtual environment, and installs the dependencies recorded in `uv.lock`.

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
├── docs/
│   ├── macos-setup.md
│   └── windows-setup.md
├── pyproject.toml
└── README.md
```

## Next step

Module 02 introduces Projects as REST resources and implements CRUD operations.
