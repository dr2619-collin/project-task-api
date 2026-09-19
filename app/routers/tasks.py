"""HTTP endpoints for the Task resource."""

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_task_service
from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.task import Task
from app.routers.http_errors import project_not_found, task_not_found
from app.schemas.tasks import TaskInput, TaskResponse
from app.services.tasks import TaskService

# Routers validate input, call services, and translate outcomes to HTTP.
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List all tasks",
    description="Return every task currently stored by the application.",
)
def list_tasks(service: TaskService = Depends(get_task_service)) -> list[Task]:
    """Delegate Task retrieval to the service layer."""
    return service.list_tasks()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get one task",
    description="Return the task identified by the path parameter.",
    responses={404: {"description": "Task not found"}},
)
def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Return one Task or translate the missing-resource error."""
    try:
        return service.get_task(task_id)
    except TaskNotFoundError:
        raise task_not_found() from None


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description="Create a task and associate it with an existing project.",
    responses={404: {"description": "Related project not found"}},
)
def create_task(
    data: TaskInput,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Create a Task after the service verifies its business rules."""
    try:
        return service.create_task(data)
    except ProjectNotFoundError:
        raise project_not_found() from None


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Replace a task",
    description="Replace all editable fields and verify the related project.",
    responses={404: {"description": "Task or related project not found"}},
)
def replace_task(
    task_id: int,
    data: TaskInput,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Replace a Task after checking both related resources."""
    try:
        return service.replace_task(task_id, data)
    except TaskNotFoundError:
        raise task_not_found() from None
    except ProjectNotFoundError:
        raise project_not_found() from None


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete the task identified by the path parameter.",
    responses={404: {"description": "Task not found"}},
)
def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> Response:
    """Delete a Task and translate the service outcome into HTTP."""
    try:
        service.delete_task(task_id)
    except TaskNotFoundError:
        raise task_not_found() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
