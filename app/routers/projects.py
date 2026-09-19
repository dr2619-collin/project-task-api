"""HTTP endpoints for the Project resource."""

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_project_service
from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.routers.http_errors import project_has_tasks, project_not_found
from app.schemas.projects import ProjectInput, ProjectResponse
from app.schemas.tasks import TaskResponse
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


# GET /projects reads the entire Project collection.
@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="Return every project currently stored by the application.",
)
def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> list[Project]:
    """Delegate Project retrieval to the service layer."""
    return service.list_projects()


# The value inside {project_id} is supplied by the URL path.
@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get one project",
    description="Return the project identified by the path parameter.",
    responses={404: {"description": "Project not found"}},
)
def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Return one Project or translate the missing-resource error."""
    try:
        return service.get_project(project_id)
    except ProjectNotFoundError:
        raise project_not_found() from None


# POST creates a new resource, so a successful request returns HTTP 201.
@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Create a project from a validated name and description.",
)
def create_project(
    data: ProjectInput,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Pass validated input to the business and persistence layers."""
    return service.create_project(data)


# PUT replaces the editable values of the Project identified by the URL.
@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Replace a project",
    description="Replace all editable fields of an existing project.",
    responses={404: {"description": "Project not found"}},
)
def replace_project(
    project_id: int,
    data: ProjectInput,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Replace one Project through the service layer."""
    try:
        return service.replace_project(project_id, data)
    except ProjectNotFoundError:
        raise project_not_found() from None


# A successful DELETE has no response body, so it returns HTTP 204.
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project only when it has no related tasks.",
    responses={
        404: {"description": "Project not found"},
        409: {"description": "Project still has related tasks"},
    },
)
def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> Response:
    """Translate Project deletion outcomes into HTTP responses."""
    try:
        service.delete_project(project_id)
    except ProjectNotFoundError:
        raise project_not_found() from None
    except ProjectHasTasksError:
        raise project_has_tasks() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# This nested URL reads the Tasks that belong to one Project.
@router.get(
    "/{project_id}/tasks",
    response_model=list[TaskResponse],
    summary="List a project's tasks",
    description="Return every task that belongs to the requested project.",
    responses={404: {"description": "Project not found"}},
)
def list_project_tasks(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> list[Task]:
    """Return related Tasks after the service verifies the Project."""
    try:
        return service.list_project_tasks(project_id)
    except ProjectNotFoundError:
        raise project_not_found() from None
