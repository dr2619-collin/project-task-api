"""HTTP endpoints for the Project resource."""

from fastapi import APIRouter, Body, HTTPException, Response, status

from app.storage import Project, Task, projects, tasks

# Every route in this file begins with /projects and appears under the
# Projects heading in FastAPI's generated API documentation.
router = APIRouter(prefix="/projects", tags=["Projects"])

def find_project(project_id: int) -> Project:
    """Find one project or return an HTTP 404 error to the client."""
    for project in projects:
        if project["id"] == project_id:
            return project

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )


# GET /projects reads the entire Project collection.
@router.get("", summary="List all projects")
def list_projects() -> list[Project]:
    """Return every project currently stored in memory."""
    return projects


# The value inside {project_id} is supplied by the URL path.
@router.get("/{project_id}", summary="Get one project")
def get_project(project_id: int) -> Project:
    """Return the project with the requested ID."""
    return find_project(project_id)


# POST creates a new resource, so a successful request returns HTTP 201.
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
)
def create_project(
    name: str = Body(),
    description: str = Body(),
) -> Project:
    """Create a project from values in the JSON request body."""
    # Generate the next ID from the existing in-memory collection.
    next_project_id = max((int(project["id"]) for project in projects), default=0) + 1
    project: Project = {
        "id": next_project_id,
        "name": name,
        "description": description,
    }
    projects.append(project)
    return project


# PUT replaces the editable values of the Project identified by the URL.
@router.put("/{project_id}", summary="Replace a project")
def replace_project(
    project_id: int,
    name: str = Body(),
    description: str = Body(),
) -> Project:
    """Replace the name and description of an existing project."""
    project = find_project(project_id)
    project.update(name=name, description=description)
    return project


# A successful DELETE has no response body, so it returns HTTP 204.
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
def delete_project(project_id: int) -> Response:
    """Remove a project from the in-memory collection."""
    project = find_project(project_id)

    # Do not leave Tasks pointing to a Project that no longer exists.
    if any(task["project_id"] == project_id for task in tasks):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delete the project's tasks before deleting the project",
        )

    projects.remove(project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# This nested URL reads the Tasks that belong to one Project.
@router.get("/{project_id}/tasks", summary="List a project's tasks")
def list_project_tasks(project_id: int) -> list[Task]:
    """Return every task associated with the requested project."""
    find_project(project_id)
    return [task for task in tasks if task["project_id"] == project_id]
