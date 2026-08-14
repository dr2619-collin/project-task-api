"""HTTP endpoints for the Task resource."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate
from app.services.tasks import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
# FastAPI calls get_db before a route runs, then passes its yielded Session into
# the `session` parameter wherever DatabaseSession appears below.
DatabaseSession = Annotated[Session, Depends(get_db)]


def task_not_found() -> HTTPException:
    """Translate a service-layer exception into an HTTP response."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Task not found",
    )


def project_not_found() -> HTTPException:
    """Describe a missing Project referenced by a Task operation."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found",
    )


@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List all tasks",
    description="Return every task currently stored by the application.",
)
def list_tasks(session: DatabaseSession) -> list[Task]:
    """Delegate Task retrieval to the service layer."""
    return TaskService(session).list_tasks()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get one task",
    description="Return the task identified by the path parameter.",
    responses={404: {"description": "Task not found"}},
)
def get_task(task_id: int, session: DatabaseSession) -> Task:
    """Return one Task or translate the missing-resource error."""
    try:
        return TaskService(session).get_task(task_id)
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
def create_task(data: TaskCreate, session: DatabaseSession) -> Task:
    """Create a Task after the service verifies its business rules."""
    try:
        return TaskService(session).create_task(data)
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
    data: TaskUpdate,
    session: DatabaseSession,
) -> Task:
    """Replace a Task after checking both related resources."""
    try:
        return TaskService(session).replace_task(task_id, data)
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
def delete_task(task_id: int, session: DatabaseSession) -> Response:
    """Delete a Task and translate the service outcome into HTTP."""
    try:
        TaskService(session).delete_task(task_id)
    except TaskNotFoundError:
        raise task_not_found() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
