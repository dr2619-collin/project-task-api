"""FastAPI application for the Project and Task Management API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  # Register ORM models before create_all().
from app.database.base import Base
from app.database.session import engine
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router

# Tag descriptions organize related operations and explain each resource group
# in Swagger UI and ReDoc.
tags_metadata = [
    {
        "name": "General",
        "description": "Basic application information and health checks.",
    },
    {
        "name": "Projects",
        "description": "Create and manage projects and view their related tasks.",
    },
    {
        "name": "Tasks",
        "description": "Create and manage tasks that belong to projects.",
    },
]


# The course demo creates missing tables at startup. This keeps the first
# persistence module focused on ORM models, sessions, and application layers.
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create missing course-demo tables when the application starts."""
    Base.metadata.create_all(bind=engine)
    yield


# Create the FastAPI application object that Uvicorn will load and run.
# This metadata is also displayed in the generated API documentation.
app = FastAPI(
    title="Project and Task Management API",
    description=(
        "Manage projects and their associated tasks. This course demonstration "
        "shows how FastAPI, layered application code, SQLAlchemy, and PostgreSQL "
        "work together to provide persistent REST resources."
    ),
    version="0.6.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# Add every Project route defined in app/routers/projects.py to the application.
# Keeping resource routes in a router prevents main.py from becoming crowded.
app.include_router(projects_router)
app.include_router(tasks_router)


# This decorator connects an HTTP GET request for "/" to read_root().
@app.get("/", tags=["General"], summary="Introduce the API")
def read_root() -> dict[str, str]:
    """Return a short introduction to the API."""
    # FastAPI converts the returned Python dictionary into a JSON response.
    return {"message": "Project and Task Management API"}


# The health endpoint gives clients a simple way to confirm the API is running.
@app.get("/health", tags=["General"], summary="Check API health")
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""
    # A successful request receives HTTP 200 and this JSON response body.
    return {"status": "healthy"}
