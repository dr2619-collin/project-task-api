"""HTTP endpoints for the Project resource."""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from app.auth.dependencies import (
    ADMIN_RESPONSES,
    AUTHENTICATED_RESPONSES,
    AdminUser,
    CurrentUser,
)
from app.dependencies import get_project_service
from app.models.project import Project
from app.models.task import Task
from app.schemas.problem_details import (
    CONFLICT_PROBLEM_RESPONSE,
    PROJECT_NOT_FOUND_RESPONSE,
    VALIDATION_PROBLEM_RESPONSE,
)
from app.schemas.projects import ProjectInput, ProjectResponse
from app.schemas.tasks import TaskResponse
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


# GET /projects reads the entire Project collection.
# `_current_user` is intentionally unused: declaring the dependency makes
# FastAPI validate the Bearer token and reject unauthenticated requests first.
@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="Return every project currently stored by the application.",
    responses=AUTHENTICATED_RESPONSES,
)
def list_projects(
    _current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> list[Project]:
    """Delegate Project retrieval to the service layer."""
    return service.list_projects()


# Keep the fixed route above /{project_id}, where "stream" would not be an int.
async def project_update_events() -> AsyncIterator[str]:
    """Yield a finite sequence of demonstration Project update events."""
    for sequence in range(1, 4):
        payload = json.dumps(
            {"sequence": sequence, "message": "Demonstration project update"}
        )
        yield f"event: project-update\ndata: {payload}\n\n"
        if sequence < 3:
            await asyncio.sleep(0.25)


@router.get(
    "/stream",
    summary="Stream demonstration project updates",
    description="Send a finite sequence of project-update events over HTTP.",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "A finite Server-Sent Event-style project update stream.",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        },
        **AUTHENTICATED_RESPONSES,
    },
)
async def stream_project_updates(_current_user: CurrentUser) -> StreamingResponse:
    """Return a protected stream without opening a database session."""
    return StreamingResponse(project_update_events(), media_type="text/event-stream")


# The value inside {project_id} is supplied by the URL path.
@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get one project",
    description="Return the project identified by the path parameter.",
    responses={
        **AUTHENTICATED_RESPONSES,
        404: PROJECT_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def get_project(
    project_id: int,
    _current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Return one Project; the global handler represents domain errors as HTTP."""
    return service.get_project(project_id)


# POST creates a new resource, so a successful request returns HTTP 201.
@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Create a project from a validated name and description.",
    responses={**ADMIN_RESPONSES, 422: VALIDATION_PROBLEM_RESPONSE},
)
def create_project(
    data: ProjectInput,
    _admin_user: AdminUser,
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
    responses={
        **ADMIN_RESPONSES,
        404: PROJECT_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def replace_project(
    project_id: int,
    data: ProjectInput,
    _admin_user: AdminUser,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Replace one Project through the service layer."""
    return service.replace_project(project_id, data)


# A successful DELETE has no response body, so it returns HTTP 204.
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project only when it has no related tasks.",
    responses={
        **ADMIN_RESPONSES,
        404: PROJECT_NOT_FOUND_RESPONSE,
        409: CONFLICT_PROBLEM_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def delete_project(
    project_id: int,
    _admin_user: AdminUser,
    service: ProjectService = Depends(get_project_service),
) -> Response:
    """Delete a Project; global handlers translate domain outcomes to HTTP."""
    service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# This nested URL reads the Tasks that belong to one Project.
@router.get(
    "/{project_id}/tasks",
    response_model=list[TaskResponse],
    summary="List a project's tasks",
    description="Return every task that belongs to the requested project.",
    responses={
        **AUTHENTICATED_RESPONSES,
        404: PROJECT_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def list_project_tasks(
    project_id: int,
    _current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> list[Task]:
    """Return related Tasks after the service verifies the Project."""
    return service.list_project_tasks(project_id)
