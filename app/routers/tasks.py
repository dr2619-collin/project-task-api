"""HTTP endpoints for the Task resource."""

from fastapi import APIRouter, Depends, Response, status

from app.auth.dependencies import (
    ADMIN_RESPONSES,
    AUTHENTICATED_RESPONSES,
    AdminUser,
    CurrentUser,
)
from app.dependencies import get_task_service
from app.models.task import Task
from app.schemas.problem_details import (
    PROJECT_NOT_FOUND_RESPONSE,
    RELATED_RESOURCE_NOT_FOUND_RESPONSE,
    TASK_NOT_FOUND_RESPONSE,
    VALIDATION_PROBLEM_RESPONSE,
)
from app.schemas.tasks import TaskInput, TaskResponse
from app.services.tasks import TaskService

# Routers validate input, call services, and translate outcomes to HTTP.
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List all tasks",
    description="Return every task currently stored by the application.",
    responses=AUTHENTICATED_RESPONSES,
)
def list_tasks(
        _current_user: CurrentUser,
        service: TaskService = Depends(get_task_service)) -> list[Task]:
    """Delegate Task retrieval to the service layer."""
    return service.list_tasks()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get one task",
    description="Return the task identified by the path parameter.",
    responses={
        **AUTHENTICATED_RESPONSES,
        404: TASK_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def get_task(
    task_id: int,
    _current_user: CurrentUser,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Return one Task; the global handler represents domain errors as HTTP."""
    return service.get_task(task_id)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description="Create a task and associate it with an existing project.",
    responses={
        **ADMIN_RESPONSES,
        404: PROJECT_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def create_task(
    data: TaskInput,
    _admin_user: AdminUser,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Create a Task after the service verifies its business rules."""
    return service.create_task(data)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Replace a task",
    description="Replace all editable fields and verify the related project.",
    responses={
        **ADMIN_RESPONSES,
        404: RELATED_RESOURCE_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def replace_task(
    task_id: int,
    data: TaskInput,
    _admin_user: AdminUser,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Replace a Task after checking both related resources."""
    return service.replace_task(task_id, data)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete the task identified by the path parameter.",
    responses={
        **ADMIN_RESPONSES,
        404: TASK_NOT_FOUND_RESPONSE,
        422: VALIDATION_PROBLEM_RESPONSE,
    },
)
def delete_task(
    task_id: int,
    _admin_user: AdminUser,
    service: TaskService = Depends(get_task_service),
) -> Response:
    """Delete a Task; the global handler translates domain outcomes to HTTP."""
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
