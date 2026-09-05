"""Temporary in-memory storage shared by the API routers."""

from app.schemas.projects import ProjectResponse
from app.schemas.tasks import TaskResponse

# These lists reset whenever the application restarts. A database and
# repository layer will replace them in a later module.
projects: list[ProjectResponse] = [
    ProjectResponse(
        id=1,
        name="Course API",
        description="Build the course demonstration API.",
    )
]

tasks: list[TaskResponse] = [
    TaskResponse(
        id=1,
        title="Create the first endpoint",
        description="Add a welcome endpoint to the FastAPI application.",
        completed=True,
        project_id=1,
    )
]
