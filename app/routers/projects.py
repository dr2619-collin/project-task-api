"""HTTP endpoints for the Project resource."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    ADMIN_RESPONSES,
    AUTHENTICATED_RESPONSES,
    AdminUser,
    CurrentUser,
)
from app.database.session import get_db
from app.exceptions import ProjectHasTasksError, ProjectNotFoundError
from app.models.project import Project
from app.models.task import Task
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.tasks import TaskResponse
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])
# FastAPI calls get_db before a route runs, then passes its yielded Session into
# the `session` parameter wherever DatabaseSession appears below.
DatabaseSession = Annotated[Session, Depends(get_db)]


def project_not_found() -> HTTPException:
    """Translate a service-layer exception into an HTTP response."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="Return every project currently stored by the application.",
    responses=AUTHENTICATED_RESPONSES,
)
def list_projects(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[Project]:
    """Return Projects after FastAPI authenticates the requesting user."""
    return ProjectService(session).list_projects()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get one project",
    description="Return the project identified by the path parameter.",
    responses={
        **AUTHENTICATED_RESPONSES,
        404: {"description": "Project not found"},
    },
)
def get_project(
    project_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Project:
    """Return one Project or translate the missing-resource error."""
    try:
        return ProjectService(session).get_project(project_id)
    except ProjectNotFoundError:
        raise project_not_found() from None


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Create a project from a validated name and description.",
    responses=ADMIN_RESPONSES,
)
def create_project(
    data: ProjectCreate,
    admin_user: AdminUser,
    session: DatabaseSession,
) -> Project:
    """Create a Project after FastAPI verifies the administrator role."""
    return ProjectService(session).create_project(data)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Replace a project",
    description="Replace all editable fields of an existing project.",
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Project not found"},
    },
)
def replace_project(
    project_id: int,
    data: ProjectUpdate,
    admin_user: AdminUser,
    session: DatabaseSession,
) -> Project:
    """Replace one Project through the service layer."""
    try:
        return ProjectService(session).replace_project(project_id, data)
    except ProjectNotFoundError:
        raise project_not_found() from None


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project only when it has no related tasks.",
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Project not found"},
        409: {"description": "Project still has related tasks"},
    },
)
def delete_project(
    project_id: int,
    admin_user: AdminUser,
    session: DatabaseSession,
) -> Response:
    """Translate Project deletion outcomes into HTTP responses."""
    try:
        ProjectService(session).delete_project(project_id)
    except ProjectNotFoundError:
        raise project_not_found() from None
    except ProjectHasTasksError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delete the project's tasks before deleting the project",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/tasks",
    response_model=list[TaskResponse],
    summary="List a project's tasks",
    description="Return every task that belongs to the requested project.",
    responses={
        **AUTHENTICATED_RESPONSES,
        404: {"description": "Project not found"},
    },
)
def list_project_tasks(
    project_id: int,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[Task]:
    """Return related Tasks after the service verifies the Project."""
    try:
        return ProjectService(session).list_project_tasks(project_id)
    except ProjectNotFoundError:
        raise project_not_found() from None
