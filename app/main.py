"""FastAPI application for the Project and Task Management API."""

from fastapi import FastAPI

from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router

# Create the FastAPI application object that Uvicorn will load and run.
# This metadata is also displayed in the generated API documentation.
app = FastAPI(
    title="Project and Task Management API",
    description="A course demonstration API for managing projects and tasks.",
    version="0.2.0",
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
